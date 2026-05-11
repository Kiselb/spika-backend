from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, security
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

router = APIRouter(prefix="/auth", tags=["auth"])

load_dotenv()

# Настройки JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
BOT_SECRET_KEY = os.getenv("BOT_SECRET_KEY")

SUBJECT_ROLE_ID = 1

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": str(expire)})
    token = jwt.encode(claims=data, key=SECRET_KEY, algorithm=ALGORITHM)
    return token

@router.post("/register", response_model=schemas.Token)
def register(user_data: schemas.UserCreateWithPassword, db: Session = Depends(get_db)):
    # Проверка уникальности email
    if db.query(models.User).filter(models.User.email == user_data.Email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    # Создаём пользователя с хешированным паролем
    user = models.User(
        first_name=user_data.Names.First if user_data.Names else None,
        last_name=user_data.Names.Last if user_data.Names else None,
        middle_name=user_data.Names.Middle if user_data.Names else None,
        position=user_data.Position,
        education_id=user_data.Education,
        email=user_data.Email,
        telegram=user_data.Telegram,
        date_of_birth=user_data.DateOfBirth,
        gender=user_data.Gender.value if user_data.Gender else None,
        married=user_data.Married,
        children=user_data.Children,
        hashed_password=security.hash_password(user_data.password)
    )
    db.add(user)
    db.flush()  # Получаем user.user_id, не фиксируя транзакцию

    # Назначаем роль «Испытуемый»
    user_role = models.UserRole(user_id=user.user_id, role_id=SUBJECT_ROLE_ID)
    db.add(user_role)

    # Фиксируем всё вместе
    db.commit()
    db.refresh(user)

    print(f"Registered new user: {user.email} with ID {user.user_id} and role 'Испытуемый'")

    # Выдаём токен
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not user.hashed_password or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/telegram-login", response_model=schemas.Token)
def telegram_login(login_data: schemas.TelegramLoginRequest, db: Session = Depends(get_db)):
    # Проверяем секретный ключ бота
    if login_data.bot_secret != BOT_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid bot secret")

    # Ищем пользователя по telegram_id (или telegram-username)
    user = db.query(models.User).filter(models.User.telegram_id == login_data.telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Генерируем JWT токен для найденного пользователя
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}
