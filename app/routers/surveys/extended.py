from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database import get_db
from ... import models, schemas
from ... import security
from ...constants import SurveyStateEnum, RoleEnum, ConclusionTypeEnum
from .common import get_survey_or_404, build_survey_out, answer_question_internal, generic_conclude
from .ai import ai_conclusion_questions05, ai_conclusion_questions38, ai_conclusion_values

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
    survey = models.Survey(survey_state=SurveyStateEnum.PREPARED, survey_start_date=datetime.now())
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

@router.post("/{user_id}/Conclusion/{type_id}", response_model=schemas.SurveyOut)
def conclude_survey(
    user_id: int,
    type_id: str,
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER, RoleEnum.EXPERT)),
    db: Session = Depends(get_db)
):
    """Заключение по первым 5 вопросам."""
    # Ищем пользователя, для которого создаём опрос
    subject_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not subject_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if type_id == ConclusionTypeEnum.QUESTIONS_05:
        return generic_conclude(
            subject_user=subject_user,
            db=db,
            conclusion_func=ai_conclusion_questions05
        )
    if type_id == ConclusionTypeEnum.QUESTIONS_38:
        return generic_conclude(
            subject_user=subject_user,
            db=db,
            conclusion_func=ai_conclusion_questions38
        )
    if type_id == ConclusionTypeEnum.VALUES:
        return generic_conclude(
            subject_user=subject_user,
            db=db,
            conclusion_func=ai_conclusion_values
        )
    raise HTTPException(status_code=400, detail="Invalid conclusion type")

@router.post("/{survey_id}/Answer/{question_id}")
def answer_question(survey_id: int, question_id: int, answer_data: schemas.SurveyAnswerRequest,
                    current_user: models.User = Depends(security.require_role(RoleEnum.EXPERT)),
                    db: Session = Depends(get_db)):
    return answer_question_internal(
        survey_id=survey_id,
        question_id=question_id,
        answer_data=answer_data,
        current_user=current_user,
        db=db
    )


