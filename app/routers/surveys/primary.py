from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.routers.surveys.extended import get_and_check_survey
from ...database import get_db
from ... import models, schemas
from ... import security
from ...constants import SurveyStateEnum, RoleEnum
from .common import get_survey_or_404, build_survey_out, answer_question_internal, save_conclusion_05, save_conclusion_38, save_conclusion_values, try_complete_survey

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

    print(f"Пользователь {current_user.user_id} запрашивает заключение по первым 5 вопросам.")

    survey = get_and_check_survey(current_user.user_id, db, SurveyStateEnum.INITIALIZED)

    print(f"Подготовка к генерации заключения по первым 5 вопросам для опроса {survey.survey_id}. Состояние опроса: {survey.survey_state}. Запускаем функцию заключения.")
    survey = save_conclusion_05(survey, db, salary_data=salary_data)
    print(f"Заключение по первым 5 вопросам для опроса {survey.survey_id} сохранено. Заключение: {survey.survey_conclusion_q05}")
    try_complete_survey(survey, db)
    print(f"Проверка на завершение опроса после сохранения заключения по первым 5 вопросам для опроса {survey.survey_id}. Состояние опроса: {survey.survey_state}.")
    db.commit()

    return build_survey_out(survey, db)

@router.post("/Conclusion/Questions38", response_model=schemas.SurveyOut)
def conclude_questions38(
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):    
    """Заключение по первым 38 вопросам."""

    print(f"Пользователь {current_user.user_id} запрашивает заключение по первым 38 вопросам.")

    survey = get_and_check_survey(current_user.user_id, db, SurveyStateEnum.INITIALIZED)
    survey = save_conclusion_38(survey, db)
    try_complete_survey(survey, db)
    db.commit()

    return build_survey_out(survey, db)

@router.post("/Conclusion/Values", response_model=schemas.SurveyOut)
def conclude_values(
    current_user: models.User = Depends(security.require_role(RoleEnum.SUBJECT)),
    db: Session = Depends(get_db)
):
    """Заключение по ценностям."""

    print(f"Пользователь {current_user.user_id} запрашивает заключение по ценностям.")

    survey = get_and_check_survey(current_user.user_id, db, SurveyStateEnum.INITIALIZED)
    survey = save_conclusion_values(survey, db)
    try_complete_survey(survey, db)
    db.commit()

    return build_survey_out(survey, db)

@router.delete("/", status_code=204)
def delete_my_survey(
    current_user: models.User = Depends(security.require_role(RoleEnum.DEVELOPER)),
    db: Session = Depends(get_db)
):
    """Удалить опрос текущего пользователя (DEVELOPER) и все связанные данные."""
    if current_user.survey_id is None:
        raise HTTPException(status_code=404, detail="No survey assigned to user")

    survey_id = current_user.survey_id

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

    # Отвязываем опрос от пользователя
    current_user.survey_id = None

    # Удаляем сам опрос
    db.query(models.Survey).filter(
        models.Survey.survey_id == survey_id
    ).delete()

    db.commit()
    return Response(status_code=204)
