from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database import get_db
from ... import models, schemas
from ... import security
from ...constants import SurveyStateEnum, RoleEnum
from .common import get_survey_or_404, build_survey_out, answer_question_internal, generic_conclude
from .ai import ai_conclusion_questions05, ai_conclusion_questions38, ai_conclusion_values

router = APIRouter()

@router.post("/", response_model=schemas.SurveyOut)
def create_my_survey(
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """
    Вернуть или создать (если ещё нет) опрос для текущего пользователя.
    Возвращает полную структуру опроса.
    """
    if current_user.survey_id:
        # Опрос уже существует – возвращаем его
        survey = get_survey_or_404(current_user.survey_id, db)
        return build_survey_out(survey, db)

    survey = models.Survey(
        survey_state=SurveyStateEnum.PREPARED,
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
        ua = models.UserAnswer(survey_id=survey.survey_id, question_id=q.question_id, answer_text=None)
        db.add(ua)

    current_user.survey_id = survey.survey_id
    db.commit()
    db.refresh(survey)

    return build_survey_out(survey, db)

@router.post("/Answer/{question_id}", status_code=200)
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
    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned to user")

    return answer_question_internal(
        survey_id=current_user.survey_id,
        question_id=question_id,
        answer_data=answer_data,
        current_user=current_user,
        db=db
    )

@router.post("/Conclusion/Questions05", response_model=schemas.SurveyOut)
def conclude_questions05(
    salary_data: schemas.SalaryDreamsUpdate,
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """Заключение по первым 5 вопросам."""

    if current_user.survey_id is None:
        raise HTTPException(status_code=400, detail="No survey assigned to user")
    
    survey = get_survey_or_404(current_user.survey_id, db)
    
    survey.fact_salary_level = salary_data.fact_salary_level
    survey.desired_salary_level = salary_data.desired_salary_level
    survey.able_salary_level = salary_data.able_salary_level
    survey.decent_salary_level = salary_data.decent_salary_level
    survey.dreams = salary_data.dreams
    survey.dreams_point = salary_data.dreams_point

    db.commit()
    
    return generic_conclude(
        current_user=current_user,
        db=db,
        conclusion_func=ai_conclusion_questions05
    )

@router.post("/Conclusion/Questions38", response_model=schemas.SurveyOut)
def conclude_questions38(
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """Заключение по вопросам 38."""
    return generic_conclude(
        current_user=current_user,
        db=db,
        conclusion_func=ai_conclusion_questions38
    )

@router.post("/Conclusion/Values", response_model=schemas.SurveyOut)
def conclude_values(
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """Заключение по ценностям."""
    return generic_conclude(
        current_user=current_user,
        db=db,
        conclusion_func=ai_conclusion_values
    )
