from typing import Optional

from sqlalchemy.orm import Session

from app.constants import PromptTypeEnum
from ..schemas.user import ProfileUpdate
from .. import models

def update_user_fields(user, data: ProfileUpdate):
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.middle_name is not None:
        user.middle_name = data.middle_name
    if data.position is not None:
        user.position = data.position
    if data.education_id is not None:
        user.education_id = data.education_id
    if data.email is not None:
        user.email = data.email
    if data.telegram is not None:
        user.telegram = data.telegram
    if data.date_of_birth is not None:
        user.date_of_birth = data.date_of_birth
    if data.gender is not None:
        user.gender = data.gender.value
    if data.married is not None:
        user.married = data.married
    if data.children is not None:
        user.children = data.children

def get_latest_prompt_by_type(db: Session, prompt_type_id: int) -> models.SystemPrompt:
    """Возвращает последний (с максимальным prompt_id) промпт указанного типа."""
    prompt = (
        db.query(models.SystemPrompt)
        .filter(models.SystemPrompt.prompt_type_id == prompt_type_id)
        .order_by(models.SystemPrompt.prompt_id.desc())
        .first()
    )
    
    return prompt

def get_user_answer_by_type_and_sort_order(
    db: Session,
    survey_id: int,
    question_type_id: int,
    sort_order: int
) -> Optional[models.UserAnswer]:
    """
    Возвращает UserAnswer для заданного опроса, типа вопроса и sort_order.
    Если вопрос или ответ не найден, возвращает None.
    """
    return (
        db.query(models.UserAnswer)
        .join(models.Question,
              models.UserAnswer.question_id == models.Question.question_id)
        .filter(
            models.UserAnswer.survey_id == survey_id,
            models.Question.questions_type_id == question_type_id,
            models.Question.sort_order == sort_order
        )
        .first()
    )

