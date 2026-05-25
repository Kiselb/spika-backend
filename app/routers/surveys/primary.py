from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.routers.surveys.ai import ai_reformulate_question
from app.routers.surveys.extended import get_and_check_survey
from app.schemas.survey import ReformulatedQuestionOut
from ...database import get_db
from ... import models, schemas
from ... import security
from ...constants import SurveyStateEnum, RoleEnum, AnswerState
from .common import get_survey_or_404, build_survey_out, answer_question_internal, save_conclusion_05, save_conclusion_38, save_conclusion_values, try_complete_survey

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.SurveyOut,
    description="Вернуть или создать (если ещё нет) опрос для текущего пользователя. Доступно для SUBJECT.",
    summary="Создать или получить опрос для текущего пользователя"
)
def create_my_survey(
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Вернуть или создать (если ещё нет) опрос для текущего пользователя.
    Возвращает полную структуру опроса.
    """
    print(f"Пользователь {current_user.user_id} запрашивает создание опроса.")
    if current_user.survey_id:
        # Опрос уже существует – возвращаем его
        survey = get_survey_or_404(current_user.survey_id, db)
        return build_survey_out(survey, db)

    survey = models.Survey(
        survey_state=SurveyStateEnum.INITIALIZED,
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
            answer_state_id=AnswerState.PREPARED,
            reformulated_text=None

        )
        db.add(ua)

    current_user.survey_id = survey.survey_id
    db.commit()
    
    print(f"Пользователь {current_user.user_id} создал опрос {survey.survey_id}. Возвращаем его.")

    survey = get_survey_or_404(survey.survey_id, db)

    return build_survey_out(survey, db)

@router.post(
    "/Answer/{question_id}",
    status_code=200,
    description="Ответ на вопрос {question_id} по опросу для текущего пользователя. Доступно для SUBJECT.",
    summary="Ответить на вопрос по опросу для текущего пользователя")
def answer_question_for_current_user(
    question_id: int,
    answer_data: schemas.SurveyAnswerRequest,
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
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
    return answer_question_internal(
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
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Заключение по первым 5 вопросам.
    """

    print(f"Пользователь {current_user.user_id} запрашивает заключение по первым 5 вопросам.")

    survey = get_and_check_survey(current_user.user_id, db, SurveyStateEnum.INITIALIZED)

    print(f"Подготовка к генерации заключения по первым 5 вопросам для опроса {survey.survey_id}. Состояние опроса: {survey.survey_state}. Запускаем функцию заключения.")
    survey = save_conclusion_05(survey, db, salary_data=salary_data)
    print(f"Заключение по первым 5 вопросам для опроса {survey.survey_id} сохранено. Заключение: {survey.survey_conclusion_q05}")
    survey.survey_state = SurveyStateEnum.PREPARED # Пока отключено, чтобы не блокировать тестирование остальных этапов. В реальной работе должно быть так, что после сохранения заключения по первым 5 вопросам опрос переходит в состояние PREPARED, и дальше уже можно отвечать на остальные вопросы.
    print(f"Проверка на завершение опроса после сохранения заключения по первым 5 вопросам для опроса {survey.survey_id}. Состояние опроса: {survey.survey_state}.")
    db.commit()
    print(f"Заключение по первым 5 вопросам для опроса {survey.survey_id} завершено. Состояние опроса: {survey.survey_state}. Возвращаем результат.")
    return build_survey_out(survey, db)

@router.post(
    "/Conclusion/Questions38",
    response_model=schemas.SurveyOut,
    description="Заключение по 38 вопросам. Для текущего пользователя. Доступно для SUBJECT.",
    summary="Заключение по 38 вопросам"
)
def conclude_questions38(
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):    
    """
    Заключение по 38 вопросам.
    """

    print(f"Пользователь {current_user.user_id} запрашивает заключение по первым 38 вопросам.")

    survey = get_and_check_survey(current_user.user_id, db, SurveyStateEnum.ANALYZING)
    survey = save_conclusion_38(survey, db)
    try_complete_survey(survey, db)
    db.commit()

    return build_survey_out(survey, db)

@router.post(
    "/Conclusion/Values",
    response_model=schemas.SurveyOut,
    description="Заключение по ценностям. Для текущего пользователя. Доступно для SUBJECT.",
    summary="Заключение по ценностям"
)
def conclude_values(
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Заключение по ценностям.
    """

    print(f"Пользователь {current_user.user_id} запрашивает заключение по ценностям.")

    survey = get_and_check_survey(current_user.user_id, db, SurveyStateEnum.INITIALIZED)
    survey = save_conclusion_values(survey, db)
    try_complete_survey(survey, db)
    db.commit()

    return build_survey_out(survey, db)

@router.delete(
    "/",
    status_code=204,
    description="Удалить опрос текущего пользователя (только для роли DEVELOPER) и все связанные данные. Это действие необратимо и удаляет все ответы, заключения и связи с типами мышления.",
    summary="Удалить опрос текущего пользователя"
)
def delete_my_survey(
    current_user: models.User = Depends(security.require_role(RoleEnum.DEVELOPER)),
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
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Помечает вопрос как пропущенный (skipped = True).
    """
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned to user")

    survey = get_survey_or_404(current_user.survey_id, db)

    # Проверяем состояние опроса: можно пропускать только в PREPARED или IN_PROGRESS
    if survey.survey_state not in (SurveyStateEnum.PREPARED, SurveyStateEnum.IN_PROGRESS):
        raise HTTPException(status_code=400, detail="Survey is not open for answers")

    ua = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id,
        models.UserAnswer.question_id == question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not found in this survey")

    ua.answer_state_id = AnswerState.SKIPPED
    ua.answer_text = None
    db.flush()

    answered_count = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id,
        or_(
            models.UserAnswer.answer_text != None,
            models.UserAnswer.answer_state_id == AnswerState.SKIPPED
        )
    ).count()
    if answered_count == 1 and survey.survey_state == SurveyStateEnum.PREPARED:
        survey.survey_state = SurveyStateEnum.IN_PROGRESS
    total_questions = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id
    ).count()
    print(f"Ответ на вопрос {question_id} для опроса {survey.survey_id} помечен как пропущенный. Количество отвеченных или пропущенных вопросов: {answered_count}/{total_questions}. Состояние опроса после пропуска: {survey.survey_state}.")
    if answered_count == total_questions:
        survey.survey_state = SurveyStateEnum.ANALYZING
        survey.survey_finish_date = datetime.now()
    print(f"Ответ на вопрос {question_id} для опроса {survey.survey_id} сохранён. Количество отвеченных вопросов: {answered_count}/{total_questions}. Состояние опроса после ответа: {survey.survey_state}.")

    db.commit()

    return {"status": "ok", "skipped": True}

@router.post(
    "/Reformulate/{question_id}",
    response_model=schemas.survey.ReformulatedQuestionOut,
    description="Переформулировать вопрос {question_id} для опроса текущего пользователя. Доступно для SUBJECT.",
    summary="Переформулировать вопрос"
)
def reformulate_question(
    question_id: int,
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Генерирует переформулировку вопроса с помощью ИИ и сохраняет её в опросе.
    """
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned to user")

    survey = get_survey_or_404(current_user.survey_id, db)

    if survey.survey_state not in (SurveyStateEnum.PREPARED, SurveyStateEnum.IN_PROGRESS):
        raise HTTPException(status_code=400, detail="Survey is not open for answers")

    ua = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id,
        models.UserAnswer.question_id == question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not found in this survey")

    # Получаем оригинальный текст вопроса
    question_text = ua.question.question_text

    # Вызываем ИИ-переформулировку
    new_text = ai_reformulate_question(question_text)

    # Сохраняем результат
    ua.reformulated_text = new_text
    db.commit()

    return schemas.survey.ReformulatedQuestionOut(reformulated_text=new_text)
