from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.routers.surveys.ai import ai_reformulate_question, ai_transform_question
from app.routers.surveys.extended import get_and_check_survey
from app.schemas.survey import ReformulatedQuestionOut
from ... database import get_db
from ... import models
from ... import schemas
from ... import security
from ... import constants
from . import common #import get_survey_or_404, build_survey_out, answer_question_internal, save_conclusion_05, save_conclusion_15, save_conclusion_38, save_dialog_conclusion_38, save_dialog_question_38, try_complete_survey

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.SurveyOut,
    description="Вернуть или создать (если ещё нет) опрос для текущего пользователя. Доступно для SUBJECT.",
    summary="Создать или получить опрос для текущего пользователя"
)
def create_my_survey(
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Вернуть или создать (если ещё нет) опрос для текущего пользователя.
    Возвращает полную структуру опроса.
    """
    print(f"Пользователь {current_user.user_id} запрашивает создание опроса.")
    if current_user.survey_id:
        # Опрос уже существует – возвращаем его
        survey = common.get_survey_or_404(current_user.survey_id, db)
        return common.build_survey_out(survey, db)

    survey = models.Survey(
        survey_state_id=constants.SurveyStateEnum.CREATED,
        survey_start_date=datetime.now()
    )
    db.add(survey)
    db.flush()

    active_questions = (
        db.query(models.Question)
        .filter(models.Question.active == True)
        .order_by(models.Question.sort_order)
        .all()
    )
    for q in active_questions:
        ua = models.UserAnswer(
            survey_id=survey.survey_id,
            question_id=q.question_id,
            answer_text=None,
            answer_state_id=constants.AnswerState.PREPARED,
            reformulated_text=None

        )
        db.add(ua)

    current_user.survey_id = survey.survey_id
    db.commit()
    
    print(f"Пользователь {current_user.user_id} создал опрос {survey.survey_id}. Возвращаем его.")

    survey = common.get_survey_or_404(survey.survey_id, db)

    return common.build_survey_out(survey, db)

@router.post(
    "/Answer/{question_id}",
    status_code=200,
    description="Ответ на вопрос {question_id} по опросу для текущего пользователя. Доступно для SUBJECT.",
    summary="Ответить на вопрос по опросу для текущего пользователя")
def answer_question_for_current_user(
    question_id: int,
    answer_data: schemas.SurveyAnswerRequest,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Ответ на вопрос для опроса текущего пользователя.
    survey_id определяется по текущему пользователю из токена.
    """
    print(f"Пользователь {current_user.user_id} запрашивает ответ на вопрос {question_id}. Проверяем наличие опроса у пользователя.")
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned to user")
    print(f"Пользователь {current_user.user_id} имеет опрос {current_user.survey_id}. Передаем управление функции сохранения ответа на вопрос.")
    return common.answer_question_internal(
        survey_id=current_user.survey_id,
        question_id=question_id,
        answer_data=answer_data,
        current_user=current_user,
        db=db
    )

@router.post(
    "/Conclusion/Questions05",
    response_model=schemas.SurveyOut,
    description="Заключение по первым 5 вопросам. Для текущего пользователя. Доступно для SUBJECT.",
    summary="Заключение по первым 5 вопросам"
)
def conclude_questions05(
    salary_data: schemas.SalaryDreamsUpdate,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Заключение по первым 5 вопросам.
    """
    print(f"Пользователь {current_user.user_id} запрашивает заключение по первым 5 вопросам.")
    survey = get_and_check_survey(current_user.user_id, db, constants.SurveyStateEnum.Q05_COMPLETED)
    print(f"Подготовка к генерации заключения по первым 5 вопросам для опроса {survey.survey_id}. Состояние опроса: {survey.survey_state_id}. Запускаем функцию заключения.")
    survey = common.save_conclusion_05(survey, db, salary_data=salary_data)
    print(f"Заключение по первым 5 вопросам для опроса {survey.survey_id} сохранено. Заключение: {survey.survey_conclusion_q05}")
    survey.survey_state_id = constants.SurveyStateEnum.Q05_ANALYZED
    print(f"Проверка на завершение опроса после сохранения заключения по первым 5 вопросам для опроса {survey.survey_id}. Состояние опроса: {survey.survey_state_id}.")
    db.commit()
    print(f"Заключение по первым 5 вопросам для опроса {survey.survey_id} завершено. Состояние опроса: {survey.survey_state_id}. Возвращаем результат.")
    return common.build_survey_out(survey, db)

@router.post(
    "/Conclusion/Questions38",
    response_model=schemas.SurveyOut,
    description="Заключение по 38 вопросам. Для текущего пользователя. Доступно для SUBJECT.",
    summary="Заключение по 38 вопросам"
)
def conclude_questions38(
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):    
    """
    Заключение по 38 вопросам.
    """
    print(f"Пользователь {current_user.user_id} запрашивает заключение по первым 38 вопросам.")
    survey = get_and_check_survey(current_user.user_id, db, constants.SurveyStateEnum.Q38_COMPLETED)
    survey = common.save_conclusion_38(survey, db)
    survey.survey_state_id = constants.SurveyStateEnum.Q38_ANALYZED
    common.try_complete_survey(survey, db)
    db.commit()
    return common.build_survey_out(survey, db)

@router.post(
    "/Conclusion/Questions15",
    response_model=schemas.SurveyOut,
    description="Заключение по ценностям. Для текущего пользователя. Доступно для SUBJECT.",
    summary="Заключение по ценностям"
)
def conclude_questions15(
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Заключение по ценностям.
    """
    print(f"Пользователь {current_user.user_id} запрашивает заключение по ценностям.")
    survey = get_and_check_survey(current_user.user_id, db, constants.SurveyStateEnum.Q15_COMPLETED)
    survey = common.save_conclusion_15(survey, db)
    survey.survey_state_id = constants.SurveyStateEnum.Q15_ANALYZED
    common.try_complete_survey(survey, db)
    db.commit()
    return common.build_survey_out(survey, db)

@router.delete(
    "/",
    status_code=204,
    description="Удалить опрос текущего пользователя (только для роли DEVELOPER) и все связанные данные. Это действие необратимо и удаляет все ответы, заключения и связи с типами мышления.",
    summary="Удалить опрос текущего пользователя"
)
def delete_my_survey(
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.DEVELOPER)),
    db: Session = Depends(get_db)
):
    """
    Удалить опрос текущего пользователя (только для роли DEVELOPER) и все связанные данные.
    Это действие необратимо и удаляет все ответы, заключения и связи с типами мышления."""
    if current_user.survey_id is None:
        raise HTTPException(status_code=404, detail="No survey assigned to user")

    survey_id = current_user.survey_id
    # Отвязываем опрос от пользователя
    current_user.survey_id = None
    db.flush()
    # Удаляем зависимые записи
    db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id
    ).delete()
    db.query(models.SurveyTypeOfThinking).filter(
        models.SurveyTypeOfThinking.survey_id == survey_id
    ).delete()
    db.query(models.SurveyPrompt).filter(
        models.SurveyPrompt.survey_id == survey_id
    ).delete()
    # Удаляем сам опрос
    db.query(models.Survey).filter(
        models.Survey.survey_id == survey_id
    ).delete()
    db.commit()
    return Response(status_code=204)

@router.post(
    "/SkipAnswer/{question_id}",
    status_code=200,
    description="Пропустить вопрос {question_id} для опроса текущего пользователя. Доступно для SUBJECT.",
    summary="Пропустить вопрос"
)
def skip_answer(
    question_id: int,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Помечает вопрос как пропущенный (skipped = True).
    """
    print(f"Пользователь {current_user.user_id} запрашивает пропуск вопроса {question_id}. Проверяем наличие опроса у пользователя.")
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned to user")
    print(f"Пользователь {current_user.user_id} имеет опрос {current_user.survey_id}. Передаем управление функции пропуска вопроса.")
    return common.answer_question_internal(
        survey_id=current_user.survey_id,
        question_id=question_id,
        answer_data=None,
        current_user=current_user,
        db=db,
        skip_question=True
    )

@router.post(
    "/Reformulate/{question_id}",
    response_model=schemas.survey.ReformulatedQuestionOut,
    description="Переформулирует вопрос {question_id} для опроса текущего пользователя. Доступно для SUBJECT.",
    summary="Переформулировать вопрос"
)
def reformulate_question(
    question_id: int,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Генерирует переформулировку вопроса с помощью ИИ и сохраняет её в опросе.
    """
    print(f"Пользователь {current_user.user_id} запрашивает переформулировку вопроса {question_id}. Проверяем наличие опроса у пользователя.")
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned to user")
    print(f"Пользователь {current_user.user_id} имеет опрос {current_user.survey_id}. Передаем управление функции переформулировки вопроса.")
    survey = common.get_survey_or_404(current_user.survey_id, db)
    print(f"Найден опрос {survey.survey_id}. Проверяем состояние опроса.")
    if survey.survey_state_id not in (
        constants.SurveyStateEnum.Q05_ANALYZED,
        constants.SurveyStateEnum.Q38_ANALYZED,
        constants.SurveyStateEnum.Q15_ANALYZED,
        constants.SurveyStateEnum.Q05_IN_PROGRESS,
        constants.SurveyStateEnum.Q38_IN_PROGRESS,
        constants.SurveyStateEnum.Q15_IN_PROGRESS
    ):
        raise HTTPException(status_code=400, detail="Survey is not open for answers")
    print(f"Опрос {survey.survey_id} находится в допустимом состоянии для переформулировки вопроса. Получаем данные о вопросе.")
    ua = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id,
        models.UserAnswer.question_id == question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not found in this survey")
    print(f"Найдена запись для ответа на вопрос {question_id} в опросе {survey.survey_id}. Получаем оригинальный текст вопроса для переформулировки.")
    # Получаем оригинальный текст вопроса
    question_text = ua.question.question_text
    print(f"Оригинальный текст вопроса {question_id} для опроса {survey.survey_id}: {question_text}. Вызываем ИИ для переформулировки.")
    # Вызываем ИИ-переформулировку
    new_text = ai_reformulate_question(question_text)
    print(f"Получена переформулировка вопроса {question_id} для опроса {survey.survey_id}: {new_text}. Сохраняем результат.")
    # Сохраняем результат
    ua.reformulated_text = new_text
    db.commit()
    return schemas.survey.ReformulatedQuestionOut(reformulated_text=new_text)

@router.post(
    "/Transform/{question_id}",
    response_model=schemas.survey.ReformulatedQuestionOut,
    description="Трансформирует вопрос {question_id} для опроса текущего пользователя. Доступно для SUBJECT.",
    summary="Трансформировать вопрос"
)
def reformulate_question(
    question_id: int,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Генерирует трансформированный вопроса с помощью ИИ и сохраняет его в опросе.
    """
    print(f"Пользователь {current_user.user_id} запрашивает трансформацию вопроса {question_id}. Проверяем наличие опроса у пользователя.")
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned to user")
    print(f"Пользователь {current_user.user_id} имеет опрос {current_user.survey_id}. Передаем управление функции трансформации вопроса.")
    survey = common.get_survey_or_404(current_user.survey_id, db)
    print(f"Найден опрос {survey.survey_id}. Проверяем состояние опроса.")
    if survey.survey_state_id not in (
        constants.SurveyStateEnum.Q05_ANALYZED,
        constants.SurveyStateEnum.Q38_ANALYZED,
        constants.SurveyStateEnum.Q15_ANALYZED,
        constants.SurveyStateEnum.Q05_IN_PROGRESS,
        constants.SurveyStateEnum.Q38_IN_PROGRESS,
        constants.SurveyStateEnum.Q15_IN_PROGRESS
    ):
        raise HTTPException(status_code=400, detail="Survey is not open for answers")
    print(f"Опрос {survey.survey_id} находится в допустимом состоянии для трансформации вопроса. Получаем данные о вопросе.")
    ua = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id,
        models.UserAnswer.question_id == question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not found in this survey")
    print(f"Найдена запись для ответа на вопрос {question_id} в опросе {survey.survey_id}. Получаем оригинальный текст вопроса для трансформации.")
    # Получаем оригинальный текст вопроса
    question_text = ua.question.question_text
    print(f"Оригинальный текст вопроса {question_id} для опроса {survey.survey_id}: {question_text}. Вызываем ИИ для трансформации.")
    question = db.query(models.Question).get(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    # Вызываем ИИ-переформулировку
    new_text = ai_transform_question(survey, question, db)
    print(f"Получен трансформированный вопрос {question_id} для опроса {survey.survey_id}: {new_text}. Сохраняем результат.")
    # Сохраняем результат
    ua.reformulated_text = new_text
    db.commit()
    return schemas.survey.ReformulatedQuestionOut(reformulated_text=new_text)

@router.post("/Dialog/{question_id}/Question", response_model=schemas.DialogQuestionOut)
def start_or_continue_dialog(
    question_id: int,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    print(f"Пользователь {current_user.user_id} запрашивает начало диалога для вопроса {question_id}.")
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned")
    survey = common.get_survey_or_404(current_user.survey_id, db)

    # Получаем запись ответа
    ua = db.query(models.UserAnswer).filter_by(
        survey_id=survey.survey_id, question_id=question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not in survey")

    # Определяем, какой вопрос диалога создавать
    if ua.answer_state_id == constants.AnswerStateEnum.PREPARED:
        # Первый вопрос – берём текст из Questions
        question_text = ua.question.question_text
        # Создаём запись диалога
        dialog = models.SurveysAnswersDialog(
            survey_id=survey.survey_id,
            question_id=question_id,
            dialog_pair_question=question_text
        )
        db.add(dialog)
        # Переводим ответ в INPROGRESS
        ua.answer_state_id = constants.AnswerStateEnum.INPROGRESS
        db.commit()
        db.refresh(dialog)
        return {"dialog_pair_id": dialog.dialog_pair_id, "dialog_pair_question": dialog.dialog_pair_question}

    elif ua.answer_state_id == constants.AnswerStateEnum.INPROGRESS:
        # Генерируем следующий вопрос диалога (заглушка)
        next_question = common.save_dialog_question_38(survey.survey_id, question_id)
        dialog = models.SurveysAnswersDialog(
            survey_id=survey.survey_id,
            question_id=question_id,
            dialog_pair_question=next_question
        )
        db.add(dialog)
        db.commit()
        db.refresh(dialog)
        return {"dialog_pair_id": dialog.dialog_pair_id, "dialog_pair_question": dialog.dialog_pair_question}

    else:
        raise HTTPException(status_code=400, detail="Question is not in dialog state")

@router.delete(
    "/Dialog/{question_id}/Question",
    status_code=204,
    description="Удалить диалог по вопросу и вернуть ответ в исходное состояние.",
    summary="Сбросить диалог по вопросу"
)
def delete_dialog(
    question_id: int,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    print(f"Пользователь {current_user.user_id} запрашивает удаление диалога для вопроса {question_id}.")    
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned")
    
    survey = common.get_survey_or_404(current_user.survey_id, db)
    ua = db.query(models.UserAnswer).filter_by(survey_id=survey.survey_id, question_id=question_id).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not in survey")

    # Проверяем, что диалог действительно активен (INPROGRESS)
    if ua.answer_state_id != constants.AnswerStateEnum.INPROGRESS:
        raise HTTPException(status_code=400, detail="Dialog is not in progress for this question")

    # Удаляем все диалоговые пары, связанные с этим вопросом в этом опросе
    deleted_count = db.query(models.SurveysAnswersDialog).filter_by(survey_id=survey.survey_id, question_id=question_id).delete()
    print(f"Удалено диалоговых записей: {deleted_count}")

    # Возвращаем ответ в исходное состояние
    ua.answer_state_id = constants.AnswerStateEnum.PREPARED

    db.commit()

    # 204 No Content не требует тела ответа
    return Response(status_code=204)

@router.post("/Dialog/{dialog_pair_id}/Response", status_code=200)
def answer_dialog(
    dialog_pair_id: int,
    body: schemas.DialogResponseIn,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    print(f"Пользователь {current_user.user_id} запрашивает ответ на вопрос диалога {dialog_pair_id}.")
    check_dialog_pair_id = db.query(models.SurveysAnswersDialog).get(dialog_pair_id)
    if not check_dialog_pair_id:
        raise HTTPException(status_code=404, detail="Dialog pair not found")
    # Проверяем, что диалог принадлежит текущему пользователю
    if check_dialog_pair_id.survey_id != current_user.survey_id:
        raise HTTPException(status_code=403, detail="Access denied")
    check_dialog_pair_id.dialog_pair_answer = body.response
    db.commit()
    return Response(status_code=200)

@router.post("/Dialog/{question_id}/Inference", response_model=schemas.DialogInferenceOut)
def finish_dialog(
    question_id: int,
    current_user: models.User = Depends(security.require_role(constants.RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    print(f"Пользователь {current_user.user_id} запрашивает заключение диалога для вопроса {question_id}.")
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned")
    survey_id = current_user.survey_id
    # Заглушка заключения диалога
    conclusion = common.save_dialog_conclusion_38(survey_id, question_id)
    ua = db.query(models.UserAnswer).filter_by(survey_id=survey_id, question_id=question_id).first()
    if ua:
        ua.answer_state_id = constants.AnswerStateEnum.COMPLETED
        ua.answer_text = conclusion
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Question not in survey")
    return {"conclusion": conclusion}