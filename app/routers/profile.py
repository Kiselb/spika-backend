from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from .. import models, schemas, security
from ..constants import RoleEnum

router = APIRouter(prefix="/Profile", tags=["Profile"])

def update_user_fields(user, data: schemas.ProfileUpdate):
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
        user.email = data.email # проверка уникальности должна быть выполнена до вызова этой функции
    if data.telegram is not None:
        user.telegram = data.telegram # проверка уникальности должна быть выполнена до вызова этой функции
    if data.date_of_birth is not None:
        user.date_of_birth = data.date_of_birth # datetime.strptime(data.date_of_birth, "%d-%m-%Y").date()
    if data.gender is not None:
        user.gender = data.gender.value
    if data.married is not None:
        user.married = data.married
    if data.children is not None:
        user.children = data.children

@router.get("", response_model=schemas.UserOut)
def get_profile(current_user: models.User = Depends(security.require_any_role(RoleEnum.SUBJECT, RoleEnum.EXPERT, RoleEnum.DEVELOPER)),
                db: Session = Depends(get_db)):
    # UserOut включает Survey и Roles
    user = db.query(models.User).options(
        joinedload(models.User.survey).joinedload(models.Survey.types_of_thinking),
        joinedload(models.User.roles)
    ).filter(models.User.user_id == current_user.user_id).first()
    return user

@router.put("", response_model=schemas.UserOut)
def update_profile(profile_data: schemas.ProfileUpdate,
                   current_user: models.User = Depends(security.require_any_role(RoleEnum.SUBJECT)),
                   db: Session = Depends(get_db)):
    if profile_data.email and profile_data.email != current_user.email:
        existing = db.query(models.User).filter(models.User.email == profile_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    if profile_data.telegram and profile_data.telegram != current_user.telegram:
        existing = db.query(models.User).filter(models.User.telegram == profile_data.telegram).first()
        if existing:
            raise HTTPException(status_code=400, detail="Telegram username already in use")
    update_user_fields(current_user, profile_data)
    db.commit()
    # Instead of db.refresh(current_user), fetch the user with relationships eager loaded
    user = db.query(models.User).options(
        joinedload(models.User.survey).joinedload(models.Survey.types_of_thinking),
        joinedload(models.User.roles)
    ).filter(models.User.user_id == current_user.user_id).first()
    return user
