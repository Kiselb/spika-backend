from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.schemas.security import LoginResponse, RoleSimple
from ..database import get_db
from .. import models, schemas
from datetime import datetime, timedelta, timezone
from jose import jwt
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, BOT_SECRET_KEY
from ..constants import RoleEnum

DEBUG_MODE = True  # Установите в False для продакшена

"""
Требуется доработка безопасности в части аутентификации через Telegram.
Сейчас секрет бота (BOT_SECRET_KEY) проверяется прямо в теле POST /Authentication/telegram-login,
что не является лучшей практикой. Для продакшена секрет следует передавать более защищённым способом (например, заголовок с HMAC-подписью),
а также обязательно использовать HTTPS для защиты от MITM-атак и перехвата данных.
Кроме того, стоит добавить логирование попыток входа и ошибок для мониторинга безопасности."""
router = APIRouter(prefix="/Authentication", tags=["Authentication"])

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": str(expire)}) # to_encode.update({"exp": int(expire.timestamp())})?
    token = jwt.encode(claims=data, key=SECRET_KEY, algorithm=ALGORITHM)
    return token

@router.post(
    "/telegram-login",
    response_model=schemas.Token,
    description="Вход через Telegram.",
    summary="Вход через Telegram"
)
def telegram_login(
    login_data: schemas.TelegramLoginRequest,
    db: Session = Depends(get_db)
):
    if login_data.bot_secret != BOT_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid bot secret")

    user = db.query(models.User).filter(models.User.telegram_id == login_data.telegram_id).first()

    if not user:
        if login_data.telegram:
            existing = db.query(models.User).filter(
                models.User.telegram == login_data.telegram
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Telegram username already in use"
                )
            
        # Создаём пользователя
        user = models.User(
            telegram=login_data.telegram,
            telegram_id=login_data.telegram_id,
        )
        db.add(user)
        db.flush()
        subject_role = db.query(models.Role).filter(
            models.Role.role_id == RoleEnum.SUBJECT
        ).first()
        if not subject_role:
            raise HTTPException(status_code=500, detail="Subject role not found")

        user_role = models.UserRole(user_id=user.user_id, role_id=subject_role.role_id)
        db.add(user_role)

        if DEBUG_MODE:
            additional_role = db.query(models.Role).filter(
                models.Role.role_id == RoleEnum.DEVELOPER
            ).first()
            if not additional_role:
                raise HTTPException(status_code=500, detail="Developer role not found")
            
            user_role = models.UserRole(user_id=user.user_id, role_id=additional_role.role_id)
            db.add(user_role)

            additional_role = db.query(models.Role).filter(
                models.Role.role_id == RoleEnum.EXPERT
            ).first()
            if not additional_role:
                raise HTTPException(status_code=500, detail="Expert role not found")
            
            user_role = models.UserRole(user_id=user.user_id, role_id=additional_role.role_id)
            db.add(user_role)

            additional_role = db.query(models.Role).filter(
                models.Role.role_id == RoleEnum.ADMIN
            ).first()
            if not additional_role:
                raise HTTPException(status_code=500, detail="Admin role not found")
            
            user_role = models.UserRole(user_id=user.user_id, role_id=additional_role.role_id)
            db.add(user_role)

        db.commit()
        db.refresh(user)

    user_with_roles = (
        db.query(models.User)
        .options(joinedload(models.User.roles))
        .filter(models.User.user_id == user.user_id)
        .first()
    )
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        roles=[RoleSimple.model_validate(r) for r in user_with_roles.roles]
    )
