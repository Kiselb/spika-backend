from datetime import datetime
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.routers.surveys.ai import ai_conclusion_questions05, ai_conclusion_questions38, ai_conclusion_values
from ... import models, schemas
from ...constants import SurveyStateEnum, AnswerState

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
                .joinedload(models.UserAnswer.answer_state)
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
        raise HTTPException(status_code=404, detail="User not found")
    print(f"Найден пользователь {user_id}.")
    if subject_user.survey_id is None:
        raise HTTPException(status_code=400, detail="User has no survey")
    print(f"Пользователь {user_id} имеет опрос с ID {subject_user.survey_id}. Получаем опрос и проверяем его состояние.")
    survey = get_survey_or_404(subject_user.survey_id, db)
    if survey.survey_state != survey_allowed_state:
        raise HTTPException(status_code=400, detail=f"Survey is not in {survey_allowed_state} state")
    print(f"Опрос {survey.survey_id} для пользователя {user_id} успешно получен и проверен. Состояние опроса: {survey.survey_state}.")
    return survey

def build_survey_out(
    survey: models.Survey,
    db: Session
) -> schemas.SurveyOut:
    # Формируем qa из уже загруженных answers с вопросами
    sorted_answers = sorted(survey.answers, key=lambda ua: ua.question.sort_order)
    qa_list = [
        schemas.QAItem(
            question_id=ua.question.question_id,
            question=ua.question.question_text,
            answer=ua.answer_text,
            answer_state=ua.answer_state.answer_state_name if ua.answer_state else None,
            skipped=ua.skipped,
            reformulated_text=ua.reformulated_text
        )
        for ua in sorted_answers
    ]

    # Типы мышления
    types_ids = None
    if survey.types_of_thinking:
        types_ids = [
            schemas.TypeOfThinkingOut(
                types_of_thinking_id=t.types_of_thinking_id,
                types_of_thinking_name=t.types_of_thinking_name,
            )
            for t in survey.types_of_thinking
        ]

    return schemas.SurveyOut(
        survey_id=survey.survey_id,
        survey_state=survey.survey_state,
        start_date=survey.survey_start_date,
        finish_date=survey.survey_finish_date,
        fact_salary_level=float(survey.fact_salary_level) if survey.fact_salary_level else None,
        desired_salary_level=float(survey.desired_salary_level) if survey.desired_salary_level else None,
        able_salary_level=float(survey.able_salary_level) if survey.able_salary_level else None,
        decent_salary_level=float(survey.decent_salary_level) if survey.decent_salary_level else None,
        dreams=survey.dreams,
        dreams_point=survey.dreams_point,
        qa=qa_list,
        types_of_thinking=types_ids,
        survey_conclusion_q05=survey.survey_conclusion_q05,
        survey_conclusion_q38=survey.survey_conclusion_q38,
        survey_conclusion_val=survey.survey_conclusion_val,
    )

def answer_question_internal(
    survey_id: int,
    question_id: int,
    answer_data: schemas.SurveyAnswerRequest,
    current_user: models.User,
    db: Session
):
    survey = get_survey_or_404(survey_id, db)
    print(f"Ответ на вопрос {question_id} для опроса {survey_id} от пользователя {current_user.user_id}. Состояние опроса: {survey.survey_state}. Проверяем возможность ответа на вопрос.")
    # Проверка допустимости состояния
    if survey.survey_state not in (SurveyStateEnum.PREPARED, SurveyStateEnum.IN_PROGRESS):
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
    ua.answer_text = answer_data.answer_text
    ua.answer_state_id = AnswerState.COMPLETED
    db.flush()

    answered_count = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.answer_text != None
    ).count()
    if answered_count == 1 and survey.survey_state == SurveyStateEnum.PREPARED:
        survey.survey_state = SurveyStateEnum.IN_PROGRESS
    total_questions = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id
    ).count()
    if answered_count == total_questions:
        survey.survey_state = SurveyStateEnum.ANALYZING
        survey.survey_finish_date = datetime.now()
    print(f"Ответ на вопрос {question_id} для опроса {survey_id} сохранён. Количество отвеченных вопросов: {answered_count}/{total_questions}. Состояние опроса после ответа: {survey.survey_state}.")
    db.commit()
    return {"status": "ok"}

def try_complete_survey(
    survey: models.Survey,
    db: Session
):
    if (
        survey.survey_conclusion_q05 is not None
        and survey.survey_conclusion_q38 is not None
        and survey.survey_conclusion_val is not None
        and survey.types_of_thinking
        and survey.survey_state == SurveyStateEnum.ANALYZING
    ):
        survey.survey_state = SurveyStateEnum.COMPLETED
def save_conclusion_05(
    survey: models.Survey,
    db: Session,
    salary_data: schemas.SalaryDreamsUpdate
) -> models.Survey:
    """
    Обновляет Опрос ответами на 5 вопросов, генерирует и сохраняет заключение по 5 вопросам.
    """
    survey.fact_salary_level = salary_data.fact_salary_level
    survey.desired_salary_level = salary_data.desired_salary_level
    survey.able_salary_level = salary_data.able_salary_level
    survey.decent_salary_level = salary_data.decent_salary_level
    survey.dreams = salary_data.dreams
    survey.dreams_point = salary_data.dreams_point
    db.flush()

    conclusion = ai_conclusion_questions05(survey)
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
    conclusion, types_of_thinking = ai_conclusion_questions38(survey)
    types = db.query(models.TypeOfThinking).filter(
        models.TypeOfThinking.types_of_thinking_id.in_(types_of_thinking)
    ).all()
    survey.survey_conclusion_q38 = conclusion
    survey.types_of_thinking = types
    db.flush()
    return survey

def save_conclusion_values(
    survey: models.Survey,
    db: Session
) -> models.Survey:
    """
    Генерирует и сохраняет заключение по ценностям.
    """
    conclusion = ai_conclusion_values(survey)
    survey.survey_conclusion_val = conclusion
    db.flush()
    return survey
