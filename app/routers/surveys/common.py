from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.routers.surveys.ai import ai_conclusion_questions15, ai_conclusion_questions05, ai_conclusion_questions38
from ... import models, schemas
from ...constants import QuestionsTypes, SurveyStateEnum, AnswerState

def get_survey_or_404(
    survey_id: int,
    db: Session
) -> models.Survey:
    survey = (
        db.query(models.Survey)
        .options(
            joinedload(models.Survey.types_of_thinking),
            joinedload(models.Survey.answers)
                .joinedload(models.UserAnswer.question),
            joinedload(models.Survey.answers)
                .joinedload(models.UserAnswer.answer_state),
            joinedload(models.Survey.answers)
                .joinedload(models.UserAnswer.conclusion),
        )
        .filter(models.Survey.survey_id == survey_id)
        .first()
    )
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return survey

def get_and_check_survey(
    user_id: int,
    db: Session,
    survey_allowed_state: SurveyStateEnum
) -> models.Survey:
    print(f"Получаем и проверяем опрос для пользователя {user_id}. Ожидаем состояние: {survey_allowed_state}.")
    subject_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not subject_user:
        print(f"Пользователь {user_id} не найден.")
        raise HTTPException(status_code=404, detail="User not found")
    print(f"Найден пользователь {user_id}.")
    if subject_user.survey_id is None:
        print(f"У пользователя {user_id} нет опроса.")
        raise HTTPException(status_code=400, detail="User has no survey")
    print(f"Пользователь {user_id} имеет опрос с ID {subject_user.survey_id}. Получаем опрос и проверяем его состояние.")
    survey = get_survey_or_404(subject_user.survey_id, db)
    if survey.survey_state_id != survey_allowed_state:
        print(f"Опрос {survey.survey_id} для пользователя {user_id} имеет неверное состояние {survey.survey_state_id}.")
        raise HTTPException(status_code=400, detail=f"Survey is not in {survey_allowed_state} state")
    print(f"Опрос {survey.survey_id} для пользователя {user_id} успешно получен и проверен. Состояние опроса: {survey.survey_state_id}.")
    return survey

def build_survey_out(
    survey: models.Survey,
    db: Session
) -> schemas.SurveyOut:
    sorted_answers = sorted(survey.answers, key=lambda ua: ua.question.sort_order)
    qa_list = []
    for ua in sorted_answers:
        thinking_type = ua.question.thinking_type
        thinking_type_name = thinking_type.types_of_thinking_name if thinking_type else None
        qa_list.append(
            schemas.QAItem(
                question_id=ua.question.question_id,
                question=ua.question.question_text,
                questions_type_id=ua.question.questions_type_id,
                validator_type_id=ua.question.validator_type_id,
                sort_order=ua.question.sort_order,
                answer=ua.answer_text,
                answer_state_id=ua.answer_state_id,
                reformulated_text=ua.reformulated_text,
                thinking_type_name=thinking_type_name
            )
        )

    return schemas.SurveyOut(
        survey_id=survey.survey_id,
        survey_state_id=survey.survey_state_id,
        start_date=survey.survey_start_date,
        finish_date=survey.survey_finish_date,
        fact_salary_level=float(survey.fact_salary_level) if survey.fact_salary_level else None,
        desired_salary_level=float(survey.desired_salary_level) if survey.desired_salary_level else None,
        able_salary_level=float(survey.able_salary_level) if survey.able_salary_level else None,
        decent_salary_level=float(survey.decent_salary_level) if survey.decent_salary_level else None,
        dreams=survey.dreams,
        dreams_point=survey.dreams_point,
        qa=qa_list,
        survey_conclusion_q05=survey.survey_conclusion_q05,
        survey_conclusion_q38=survey.survey_conclusion_q38,
        survey_conclusion_q15=survey.survey_conclusion_q15,
    )

def answer_question_internal(
    survey_id: int,
    question_id: int,
    answer_data: schemas.SurveyAnswerRequest,
    current_user: models.User,
    db: Session,
    skip_question: bool = False
):
    question_type_id = db.query(models.Question.questions_type_id).filter(models.Question.question_id == question_id).scalar()
    survey = get_survey_or_404(survey_id, db)
    print(f"Ответ на вопрос {question_id} для опроса {survey_id} от пользователя {current_user.user_id}. Состояние опроса: {survey.survey_state_id}. Проверяем возможность ответа на вопрос.")
    
    # Проверка допустимости состояния
    answered_count = db.query(models.UserAnswer).join(
        models.Question
    ).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.answer_state_id != AnswerState.PREPARED,
        models.Question.questions_type_id == question_type_id
    ).count()
    if answered_count > 0:
        if survey.survey_state_id not in (SurveyStateEnum.Q05_IN_PROGRESS, SurveyStateEnum.Q38_IN_PROGRESS, SurveyStateEnum.Q15_IN_PROGRESS):
            raise HTTPException(status_code=400, detail="Survey is not open for answers")
    else:
        if survey.survey_state_id not in (SurveyStateEnum.CREATED, SurveyStateEnum.Q05_ANALYZED, SurveyStateEnum.Q38_ANALYZED, SurveyStateEnum.Q15_ANALYZED):
            raise HTTPException(status_code=400, detail="Survey is not open for answers")

    print(f"Опрос {survey_id} находится в допустимом состоянии для ответа на вопрос. Проверяем принадлежность опроса пользователю.")
    # Проверка, что опрос принадлежит пользователю
    if current_user.survey_id != survey_id:
        raise HTTPException(status_code=403, detail="Access to this survey denied")
    print(f"Пользователь {current_user.user_id} имеет доступ к опросу {survey_id}. Сохраняем ответ на вопрос {question_id}.")
    ua = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.question_id == question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not found in this survey")
    print(f"Найдена запись для ответа на вопрос {question_id} в опросе {survey_id}. Сохраняем ответ.")
    if skip_question:
        ua.answer_state_id = AnswerState.SKIPPED
        ua.answer_text = None
    else:
        ua.answer_text = answer_data.answer_text
        ua.answer_state_id = AnswerState.COMPLETED
    db.flush()

    answered_count = db.query(models.UserAnswer).join(
        models.Question
    ).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.answer_state_id != AnswerState.PREPARED,
        models.Question.questions_type_id == question_type_id
    ).count()

    total_questions = db.query(models.UserAnswer).join(
        models.Question
    ).filter(
        models.UserAnswer.survey_id == survey_id,
        models.Question.questions_type_id == question_type_id
    ).count()
    if answered_count == total_questions:
        print(f"Все вопросы типа {question_type_id} в опросе {survey_id} отвечены. Количество отвеченных вопросов: {answered_count}/{total_questions}. Переходим к следующему состоянию опроса.")
        if question_type_id == 1:  # Завершение блока из 5 вопросов
            survey.survey_state_id = SurveyStateEnum.Q05_COMPLETED
        elif question_type_id == 2:  # Завершение блока из 38 вопросов
            survey.survey_state_id = SurveyStateEnum.Q38_COMPLETED
        elif question_type_id == 3:  # Завершение блока из 15 вопросов
            survey.survey_state_id = SurveyStateEnum.Q15_COMPLETED
        else:
            raise HTTPException(status_code=400, detail="Unknown question type")
    else:
        if question_type_id == 1:  # Начало блока из 5 вопросов
            survey.survey_state_id = SurveyStateEnum.Q05_IN_PROGRESS
        elif question_type_id == 2:  # Начало блока из 38 вопросов
            survey.survey_state_id = SurveyStateEnum.Q38_IN_PROGRESS
        elif question_type_id == 3:  # Начало блока из 15 вопросов
            survey.survey_state_id = SurveyStateEnum.Q15_IN_PROGRESS
        else:
            raise HTTPException(status_code=400, detail="Unknown question type")
    survey.survey_finish_date = datetime.now()
    print(f"Ответ на вопрос {question_id} для опроса {survey_id} сохранён. Количество отвеченных вопросов: {answered_count}/{total_questions}. Состояние опроса после ответа: {survey.survey_state_id}.")
    db.commit()
    return {"status": "ok"}

def try_complete_survey(
    survey: models.Survey,
    db: Session
):
    if (
        survey.survey_conclusion_q05 is not None
        and survey.survey_conclusion_q38 is not None
        and survey.survey_conclusion_q15 is not None
        and survey.types_of_thinking
    ):
        survey.survey_state_id = SurveyStateEnum.COMPLETED

def save_conclusion_05(
    survey: models.Survey,
    db: Session,
) -> models.Survey:
    """
    Обновляет Опрос ответами на 5 вопросов, генерирует и сохраняет заключение по 5 вопросам.
    """
    if survey.survey_state_id != SurveyStateEnum.Q05_COMPLETED:
        raise HTTPException(status_code=400, detail="Survey is not in Q05_COMPLETED state")

    # survey.fact_salary_level = salary_data.fact_salary_level
    # survey.desired_salary_level = salary_data.desired_salary_level
    # survey.able_salary_level = salary_data.able_salary_level
    # survey.decent_salary_level = salary_data.decent_salary_level
    # survey.dreams = salary_data.dreams
    # survey.dreams_point = salary_data.dreams_point
    # db.flush()

    conclusion = ai_conclusion_questions05(survey, db)
    survey.survey_conclusion_q05 = conclusion
    db.flush()

    return survey

def save_conclusion_38(
    survey: models.Survey,
    db: Session
) -> models.Survey:
    """
    Генерирует и сохраняет заключение по 38 вопросам.
    Сохраняет список типов мышления, который возвращает LLM.
    """
    if survey.survey_state_id != SurveyStateEnum.Q38_COMPLETED:
        raise HTTPException(status_code=400, detail="Survey is not in Q38_COMPLETED state")

    conclusion, _ = ai_conclusion_questions38(survey, db)
    survey.survey_conclusion_q38 = conclusion
    db.flush()
    return survey

def save_conclusion_15(
    survey: models.Survey,
    db: Session
) -> models.Survey:
    """
    Генерирует и сохраняет заключение по ценностям.
    """
    if survey.survey_state_id != SurveyStateEnum.Q15_COMPLETED:
        raise HTTPException(status_code=400, detail="Survey is not in Q15_COMPLETED state")

    conclusion = ai_conclusion_questions15(survey, db)
    survey.survey_conclusion_q15 = conclusion
    db.flush()
    return survey
