from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from .surveys import build_survey_out

router = APIRouter(prefix="/Users", tags=["Users"])

@router.post("/", response_model=dict, status_code=201)
def create_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверка уникальности email (уже есть UNIQUE, но для читаемой ошибки)
    if db.query(models.User).filter(models.User.email == user_data.Email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    # Создание пользователя
    user = models.User(
        first_name=user_data.Names.First,
        last_name=user_data.Names.Last,
        middle_name=user_data.Names.Middle,
        position=user_data.Position,
        education_id=user_data.Education,
        email=user_data.Email,
        telegram=user_data.Telegram,
        date_of_birth=user_data.DateOfBirth,
        gender=user_data.Gender.value,
        married=user_data.Married,
        children=user_data.Children
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"UserID": user.user_id}

@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Собираем ответ
    user_out = schemas.UserOut(
        Names=schemas.NamesOut(First=user.first_name, Last=user.last_name, Middle=user.middle_name),
        Position=user.position,
        Education=user.education_id,
        Email=user.email,
        Telegram=user.telegram,
        DateOfBirth=user.date_of_birth,
        Gender=user.gender,
        Married=user.married,
        Children=user.children,
        Survey=None
    )
    if user.survey_id:
        survey = db.query(models.Survey).filter(models.Survey.survey_id == user.survey_id).first()
        if survey:
            user_out.Survey = build_survey_out(survey, db)

    user_out.Roles = [schemas.RoleOut(role_id=r.role_id, role_name=r.role_name) for r in user.roles]
    
    return user_out
