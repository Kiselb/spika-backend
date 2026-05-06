from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, security
from datetime import datetime

router = APIRouter(prefix="/Profile", tags=["Profile"])

def update_user_fields(user, data: schemas.ProfileUpdate):
    if data.Names:
        user.first_name = data.Names.First
        user.last_name = data.Names.Last
        user.middle_name = data.Names.Middle
    if data.Position is not None:
        user.position = data.Position
    if data.Education is not None:
        user.education_id = data.Education
    if data.Email is not None:
        # проверка уникальности
        user.email = data.Email
    if data.Telegram is not None:
        user.telegram = data.Telegram
    if data.DateOfBirth is not None:
        user.date_of_birth = datetime.strptime(data.DateOfBirth, "%d-%m-%Y").date()
    if data.Gender is not None:
        user.gender = data.Gender.value
    if data.Married is not None:
        user.married = data.Married
    if data.Children is not None:
        user.children = data.Children

@router.get("", response_model=schemas.UserOut)
def get_profile(current_user: models.User = Depends(security.require_role("Испытуемый")),
                db: Session = Depends(get_db)):
    # UserOut включает Survey и Roles
    return current_user

@router.put("", response_model=schemas.UserOut)
def update_profile(profile_data: schemas.ProfileUpdate,
                   current_user: models.User = Depends(security.require_role("Испытуемый")),
                   db: Session = Depends(get_db)):
    if profile_data.Email and profile_data.Email != current_user.email:
        existing = db.query(models.User).filter(models.User.email == profile_data.Email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    update_user_fields(current_user, profile_data)
    db.commit()
    db.refresh(current_user)
    return current_user
