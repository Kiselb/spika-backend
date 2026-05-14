from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from .. import models, schemas, security
from ..constants import RoleEnum
from .utils import update_user_fields

router = APIRouter(prefix="/Profile", tags=["Profile"])

def load_current_user_profile(user_id: int, db: Session, include_survey: bool):
    """Загружает пользователя с education, roles и опционально survey"""
    options = [
        joinedload(models.User.education),
        joinedload(models.User.roles)
    ]
    if include_survey:
        options.append(joinedload(models.User.survey).joinedload(models.Survey.types_of_thinking))
    return db.query(models.User).options(*options).filter(models.User.user_id == user_id).first()


@router.get("", response_model=schemas.UserOut)
def get_profile(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # SUBJECT видит свой профиль с опросом
    is_subject = any(r.role_name == RoleEnum.SUBJECT for r in current_user.roles)
    return load_current_user_profile(current_user.user_id, db, include_survey=is_subject)


@router.put("", response_model=schemas.UserOut)
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

    is_subject = any(r.role_name == RoleEnum.SUBJECT for r in current_user.roles)
    return load_current_user_profile(current_user.user_id, db, include_survey=is_subject)