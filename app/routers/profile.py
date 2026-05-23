from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.routers.surveys.common import build_survey_out
from ..database import get_db
from .. import models, schemas, security
from ..constants import RoleEnum
from .utils import update_user_fields
from ..security import user_has_role

router = APIRouter(prefix="/Profile", tags=["Profile"])

def load_current_user_profile(user_id: int, db: Session, include_survey: bool):
    """Загружает профиль пользователя и опционально survey"""
    options = [
        joinedload(models.User.education),
        joinedload(models.User.roles)
    ]
    if include_survey:
        # Типы мышления
        options.append(
            joinedload(models.User.survey)
            .joinedload(models.Survey.types_of_thinking)
        )
        # Ответы с вопросами
        options.append(
            joinedload(models.User.survey)
            .joinedload(models.Survey.answers)
            .joinedload(models.UserAnswer.question)
        )
    return db.query(models.User).options(*options).filter(models.User.user_id == user_id).first()

@router.get(
    "",
    response_model=schemas.UserOut,
    description="Получить профиль текущего пользователя.",
    summary="Профиль пользователя"
)
def get_profile(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # SUBJECT видит свой профиль с опросом
    is_subject = user_has_role(current_user, RoleEnum.SUBJECT)
    user = load_current_user_profile(current_user.user_id, db, include_survey=is_subject)

    # Вручную строим UserOut, если есть опрос и нужен SurveyOut с QA
    # Автоматическая валидация Pydantic не сможет преобразовать атрибут answers (список объектов UserAnswer) в поле qa (список QAItem),
    # которое ожидает схема SurveyOut. Поэтому ручное построение через build_survey_out необходимо, при этом load_current_user_profile должен загружает опрос.
    user_out = schemas.UserOut.model_validate(user)  # создаёт базовый объект без survey
    if is_subject and user.survey:
        user_out.survey = build_survey_out(user.survey, db)
    return user_out

@router.put(
    "",
    response_model=schemas.UserOut,
    description="Обновить профиль текущего пользователя.",
    summary="Обновить профиль"
)
def update_profile(
    profile_data: schemas.ProfileUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # Проверки уникальности
    if profile_data.email and profile_data.email != current_user.email:
        if db.query(models.User).filter(models.User.email == profile_data.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
    if profile_data.telegram and profile_data.telegram != current_user.telegram:
        if db.query(models.User).filter(models.User.telegram == profile_data.telegram).first():
            raise HTTPException(status_code=400, detail="Telegram username already in use")

    update_user_fields(current_user, profile_data)
    db.commit()

    is_subject = user_has_role(current_user, RoleEnum.SUBJECT)
    user = load_current_user_profile(current_user.user_id, db, include_survey=is_subject)
    user_out = schemas.UserOut.model_validate(user)
    if is_subject and user.survey:
        user_out.survey = build_survey_out(user.survey, db)
    return user_out
