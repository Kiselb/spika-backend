from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, security

router = APIRouter(prefix="/Survey", tags=["Surveys"])

def get_survey_or_404(survey_id: int, db: Session) -> models.Survey:
    survey = db.query(models.Survey).filter(models.Survey.survey_id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return survey

def build_qa_sorted(survey_id: int, db: Session) -> List[schemas.QAItem]:
    results = (
        db.query(models.UserAnswer.answer_text, models.Question.question_text, models.Question.sort_order)
        .join(models.Question, models.UserAnswer.question_id == models.Question.question_id)
        .filter(models.UserAnswer.survey_id == survey_id)
        .order_by(models.Question.sort_order)
        .all()
    )
    return [schemas.QAItem(Question=q_text, Answer=ans_text) for ans_text, q_text, _ in results]

def build_survey_out(survey: models.Survey, db: Session) -> schemas.SurveyOut:
    types_ids = None
    if survey.types_of_thinking:
        types_ids = [t.types_of_thinking_id for t in survey.types_of_thinking]
    return schemas.SurveyOut(
        SurveyID=survey.survey_id,
        SurveyState=survey.survey_state,
        StartDate=survey.survey_start_date,
        FinishDate=survey.survey_finish_date,
        FactSalaryLevel=float(survey.fact_salary_level) if survey.fact_salary_level else None,
        DesiredSalaryLevel=float(survey.desired_salary_level) if survey.desired_salary_level else None,
        AbleSalaryLevel=float(survey.able_salary_level) if survey.able_salary_level else None,
        DecentSalaryLevel=float(survey.decent_salary_level) if survey.decent_salary_level else None,
        Dreams=survey.dreams,
        DreamsPoint=survey.dreams_point,
        QA=build_qa_sorted(survey.survey_id, db),
        TypesOfThinking=types_ids,
        SurveyConclusion=survey.survey_conclusion
    )

def try_complete_survey(survey: models.Survey, db: Session):
    if survey.survey_conclusion and survey.types_of_thinking:
        survey.survey_state = "ЗАВЕРШЁН"
        db.commit()

@router.post("", response_model=schemas.SurveyCreateResponse)
def create_my_survey(current_user: models.User = Depends(security.require_role("Испытуемый")),
                     db: Session = Depends(get_db)):
    if current_user.survey_id:
        return {"SurveyID": current_user.survey_id}
    survey = models.Survey(
        survey_state="ПОДГОТОВЛЕН",
        survey_start_date=datetime.now()
    )
    db.add(survey)
    db.flush()
    active_questions = db.query(models.Question).filter(models.Question.active == True).order_by(models.Question.sort_order).all()
    for q in active_questions:
        ua = models.UserAnswer(survey_id=survey.survey_id, question_id=q.question_id, answer_text=None)
        db.add(ua)
    current_user.survey_id = survey.survey_id
    db.commit()
    return {"SurveyID": survey.survey_id}

@router.post("/{survey_id}/{question_id}")
def answer_question(survey_id: int, question_id: int, answer_data: schemas.SurveyAnswerRequest,
                    current_user: models.User = Depends(security.require_role("Испытуемый")),
                    db: Session = Depends(get_db)):
    # Проверка, что опрос принадлежит пользователю
    if current_user.survey_id != survey_id:
        raise HTTPException(status_code=403, detail="Access to this survey denied")
    survey = get_survey_or_404(survey_id, db)
    ua = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.question_id == question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not found in this survey")
    ua.answer_text = answer_data.Answer
    answered_count = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.answer_text != None
    ).count()
    if answered_count == 1 and survey.survey_state == "ПОДГОТОВЛЕН":
        survey.survey_state = "ВЫПОЛНЯЕТСЯ"
    total_questions = db.query(models.UserAnswer).filter(models.UserAnswer.survey_id == survey_id).count()
    if answered_count == total_questions:
        survey.survey_state = "АНАЛИЗИРУЕТСЯ"
        survey.survey_finish_date = datetime.now()
    db.commit()
    return {"status": "ok"}

@router.post("/{survey_id}/Conclusion", response_model=schemas.SurveyOut)
def conclude_survey(survey_id: int,
                    current_user: models.User = Depends(security.require_role("Испытуемый")),
                    db: Session = Depends(get_db)):
    if current_user.survey_id != survey_id:
        raise HTTPException(status_code=403, detail="Access to this survey denied")
    survey = get_survey_or_404(survey_id, db)
    if survey.survey_state != "АНАЛИЗИРУЕТСЯ":
        raise HTTPException(status_code=400, detail="Survey is not ready for conclusion")

    # Заглушка AI-агента (в реальном проекте заменить на вызов AI-сервиса)
    conclusion_text, thinking_type_ids = ai_agent_generate_conclusion(survey, db)

    survey.survey_conclusion = conclusion_text
    # Сохраняем типы мышления
    db.query(models.SurveyTypeOfThinking).filter(models.SurveyTypeOfThinking.survey_id == survey_id).delete()
    for tid in thinking_type_ids:
        db.add(models.SurveyTypeOfThinking(survey_id=survey_id, types_of_thinking_id=tid))
    db.commit()
    db.refresh(survey)
    try_complete_survey(survey, db)
    return build_survey_out(survey, db)

def ai_agent_generate_conclusion(survey: models.Survey, db: Session):
    """
    Заглушка для AI-агента.
    Возвращает кортеж (conclusion_text: str, thinking_type_ids: list[int]).
    """
    # Пример: берём все ответы и формируем простой текст
    answers = db.query(models.UserAnswer).filter(models.UserAnswer.survey_id == survey.survey_id).all()
    conclusion = "AI analysis result based on " + str(len(answers)) + " answers."
    # Возвращаем все доступные типы мышления как пример
    types = [t.types_of_thinking_id for t in db.query(models.TypeOfThinking).all()]
    return conclusion, types
