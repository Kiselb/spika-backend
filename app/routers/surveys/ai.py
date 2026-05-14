from sqlalchemy.orm import Session
from .. import models

def ai_conclusion_questions05(survey: models.Survey, db: Session):
    """Заключение по первому блоку из 5 вопросов"""
    answers = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id
    ).all()
    conclusion = "Заключение по первому блоку из 5 вопросов: " + str(len(answers)) + " ответов."
    # Возвращаем, например, первые два типа мышления
    types = [t.types_of_thinking_id for t in db.query(models.TypeOfThinking).limit(2).all()]
    return conclusion, types

def ai_conclusion_questions38(survey: models.Survey, db: Session):
    """Заключение по второму блоку из 38 вопросов"""
    answers = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id
    ).all()
    conclusion = "Заключение по второму блоку из 38 вопросов: " + str(len(answers)) + " ответов."
    types = [t.types_of_thinking_id for t in db.query(models.TypeOfThinking).offset(2).limit(3).all()]
    return conclusion, types

def ai_conclusion_values(survey: models.Survey, db: Session):
    """Заглушка для /Survey/Conclusion/Values"""
    answers = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey.survey_id
    ).all()
    conclusion = "Ценностное заключение на основе: " + str(len(answers)) + " ответов."
    types = [t.types_of_thinking_id for t in db.query(models.TypeOfThinking).all()]
    return conclusion, types

