from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, security
from datetime import datetime

router = APIRouter(prefix="/Users", tags=["Users"])

@router.post("", response_model=schemas.UserOut, status_code=201)
def create_user(user_data: schemas.UserAdminCreate,
                db: Session = Depends(get_db),
                current_user: models.User = Depends(security.require_role("Admin"))):
    if db.query(models.User).filter(models.User.email == user_data.Email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        first_name=user_data.Names.First,
        last_name=user_data.Names.Last,
        middle_name=user_data.Names.Middle,
        position=user_data.Position,
        education_id=user_data.Education,
        email=user_data.Email,
        telegram=user_data.Telegram,
        date_of_birth=datetime.strptime(user_data.DateOfBirth, "%d-%m-%Y").date(),
        gender=user_data.Gender.value,
        married=user_data.Married,
        children=user_data.Children,
        hashed_password=security.hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db),
             current_user: models.User = Depends(security.require_role("Admin"))):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, user_data: schemas.ProfileUpdate,
                db: Session = Depends(get_db),
                current_user: models.User = Depends(security.require_role("Admin"))):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_data.Email and user_data.Email != user.email:
        if db.query(models.User).filter(models.User.email == user_data.Email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
    # Используем ту же функцию обновления, что и в профиле
    from .profile import update_user_fields  # или вынести общую логику
    update_user_fields(user, user_data)
    db.commit()
    db.refresh(user)
    return user
