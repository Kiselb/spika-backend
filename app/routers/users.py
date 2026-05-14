from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from .. import models, schemas, security
from ..constants import RoleEnum

router = APIRouter(prefix="/Users", tags=["Users"])

@router.post("", response_model=schemas.UserOut, status_code=201)
def create_user(user_data: schemas.UserCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(security.require_role(RoleEnum.ADMIN))):
    
    if db.query(models.User).filter(models.User.telegram_id == user_data.telegram_id).first():
        raise HTTPException(status_code=400, detail="User with this telegram_id already exists")
    if user_data.telegram is not None and db.query(models.User).filter(models.User.telegram == user_data.telegram).first():
        raise HTTPException(status_code=400, detail="Telegram username already in use")
    if user_data.email and db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = models.User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_name=user_data.middle_name,
        position=user_data.position,
        education_id=user_data.education_id,
        email=user_data.email,
        telegram=user_data.telegram,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender.value,
        married=user_data.married,
        children=user_data.children,
        telegram_id=user_data.telegram_id,)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db),
             current_user: models.User = Depends(security.require_role(RoleEnum.ADMIN))):
    user = db.query(models.User).options(
        joinedload(models.User.survey).joinedload(models.Survey.types_of_thinking),
        joinedload(models.User.roles)
    ).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, user_data: schemas.ProfileUpdate,
                db: Session = Depends(get_db),
                current_user: models.User = Depends(security.require_role(RoleEnum.ADMIN))):
    
    user = db.query(models.User).options(
        joinedload(models.User.survey).joinedload(models.Survey.types_of_thinking),
        joinedload(models.User.roles)
    ).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_data.telegram is not None and user_data.telegram != user.telegram:
        if db.query(models.User).filter(models.User.telegram == user_data.telegram).first():
            raise HTTPException(status_code=400, detail="Telegram username already in use")
    if user_data.email and user_data.email != user.email:
        if db.query(models.User).filter(models.User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
    # Используем ту же функцию обновления, что и в профиле
    from .profile import update_user_fields  # или вынести общую логику
    update_user_fields(user, user_data)
    db.commit()
    db.refresh(user)
    return user
