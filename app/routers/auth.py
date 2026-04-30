from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, security
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter(prefix="/auth", tags=["auth"])

# Настройки JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register", response_model=schemas.Token)
def register(user_data: schemas.UserCreateWithPassword, db: Session = Depends(get_db)):
    # Проверка уникальности email
    if db.query(models.User).filter(models.User.email == user_data.Email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    # Создаём пользователя с хешированным паролем
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
        children=user_data.Children,
        hashed_password=security.hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Сразу выдаём токен
    access_token = create_access_token(data={"sub": user.user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not user.hashed_password or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.user_id})
    return {"access_token": access_token, "token_type": "bearer"}