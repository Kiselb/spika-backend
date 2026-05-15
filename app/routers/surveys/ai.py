from http.client import HTTPException
from sqlalchemy.orm import Session
from app.constants import SurveyStateEnum
from app.routers.surveys.common import build_survey_out
from ... import models

def ai_conclusion_questions05(survey: models.Survey, db: Session):
    """Заключение по первому блоку из 5 вопросов"""
    if survey.survey_state != SurveyStateEnum.ANALYZING:
        raise HTTPException(status_code=400, detail="Survey is not in ANALYZING state")

    answers = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id
    ).all()
    conclusion = "Заключение по первому блоку из 5 вопросов: " + str(len(answers)) + " ответов."    
    survey.survey_conclusion_q05 = conclusion
    if not db.in_transaction():
        db.commit()
    return build_survey_out(survey, db)

def ai_conclusion_questions38(survey: models.Survey, db: Session):
    """Заключение по второму блоку из 38 вопросов"""
    if survey.survey_state != SurveyStateEnum.ANALYZING:
        raise HTTPException(status_code=400, detail="Survey is not in ANALYZING state")
    
    answers = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id
    ).all()
    conclusion = "Заключение по второму блоку из 38 вопросов: " + str(len(answers)) + " ответов."
    # Удаляем старые связи
    #
    #thinking_type_ids = [1, 2]  # пример новых типов мышления, которые мы хотим сохранить
    #db.query(models.SurveyTypeOfThinking).filter(
    #    models.SurveyTypeOfThinking.survey_id == survey.survey_id
    #).delete()
    # Добавляем новые типы
    #for tid in thinking_type_ids:
    #    db.add(models.SurveyTypeOfThinking(survey_id=survey.survey_id, types_of_thinking_id=tid))
    #db.flush()  # применяем изменения, но не коммитим, чтобы оставить в транзакции

    survey.survey_conclusion_val = conclusion
    if not db.in_transaction():
        db.commit()    
    return build_survey_out(survey, db)

def ai_conclusion_values(survey: models.Survey, db: Session):
    """Заглушка для /Survey/Conclusion/Values"""
    if survey.survey_state != SurveyStateEnum.ANALYZING:
        raise HTTPException(status_code=400, detail="Survey is not in ANALYZING state")
    conclusion = "Ценностное заключение"
    survey.survey_conclusion_val = conclusion
    if not db.in_transaction():
        db.commit()
    return build_survey_out(survey, db)

