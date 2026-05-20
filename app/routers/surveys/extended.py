from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database import get_db
from ... import models, schemas
from ... import security
from ...constants import SurveyStateEnum, RoleEnum
from .common import get_and_check_survey, get_survey_or_404, build_survey_out, answer_question_internal, save_conclusion_05, save_conclusion_38, save_conclusion_values, try_complete_survey

router = APIRouter()

@router.post("/{user_id}", response_model=schemas.SurveyOut)
def create_survey_for_user(
    user_id: int,
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER, RoleEnum.EXPERT)),
    db: Session = Depends(get_db)
):
    """
    Вернуть или создать (если ещё нет) опрос для указанного пользователя.
    Возвращает полную структуру опроса.
    """

    # Ищем пользователя, для которого создаём опрос
    subject_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not subject_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Если у пользователя уже есть опрос, возвращаем его
    if subject_user.survey_id:
        survey = get_survey_or_404(subject_user.survey_id, db)
        return build_survey_out(survey, db)

    # Создаём новый опрос
    survey = models.Survey(survey_state=SurveyStateEnum.INITIALIZED, survey_start_date=datetime.now())
    db.add(survey)
    db.flush()  # получаем survey.survey_id

    # Привязываем активные вопросы к опросу
    active_questions = (db.query(models.Question).filter(models.Question.active == True).order_by(models.Question.sort_order).all()
    )
    for q in active_questions:
        ua = models.UserAnswer(survey_id=survey.survey_id, question_id=q.question_id, answer_text=None)
        db.add(ua)

    # Связываем опрос с целевым пользователем
    subject_user.survey_id = survey.survey_id
    db.commit()

    return build_survey_out(survey, db)

@router.post("/{user_id}/Conclusion/Questions05", response_model=schemas.SurveyOut)
def conclude_questions05_for_user(
    user_id: int,
    salary_data: schemas.SalaryDreamsUpdate,  # тело запроса обязательно
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER, RoleEnum.EXPERT)),
    db: Session = Depends(get_db)
):
    survey = get_and_check_survey(user_id, db, SurveyStateEnum.INITIALIZED)
    survey = save_conclusion_05(survey, db, salary_data=salary_data)
    try_complete_survey(survey, db)
    db.commit()
    return build_survey_out(survey, db)

@router.post("/{user_id}/Conclusion/Questions38", response_model=schemas.SurveyOut)
def conclude_questions38_for_user(
    user_id: int,
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER, RoleEnum.EXPERT)),
    db: Session = Depends(get_db)
):
    survey = get_and_check_survey(user_id, db, SurveyStateEnum.ANALYZING)
    survey = save_conclusion_38(survey, db)   # без данных, только генерация
    try_complete_survey(survey, db)
    db.commit()
    return build_survey_out(survey, db)

@router.post("/{user_id}/Conclusion/Values", response_model=schemas.SurveyOut)
def conclude_values_for_user(
    user_id: int,
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER, RoleEnum.EXPERT)),
    db: Session = Depends(get_db)
):
    survey = get_and_check_survey(user_id, db, SurveyStateEnum.ANALYZING)
    survey = save_conclusion_values(survey, db)
    try_complete_survey(survey, db)
    db.commit()
    return build_survey_out(survey, db)

@router.post("/{survey_id}/Answer/{question_id}")
def answer_question(
    survey_id: int,
    question_id: int,
    answer_data: schemas.SurveyAnswerRequest,
    current_user: models.User = Depends(security.require_role(RoleEnum.EXPERT)),
    db: Session = Depends(get_db)
):
    return answer_question_internal(
        survey_id=survey_id,
        question_id=question_id,
        answer_data=answer_data,
        current_user=current_user,
        db=db
    )
