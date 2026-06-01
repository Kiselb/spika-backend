from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.constants import RoleEnum
from .database import get_db
from . import models
from .config import SECRET_KEY, ALGORITHM

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials  # токен без "Bearer "
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=ALGORITHM)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).options(joinedload(models.User.roles)).filter(models.User.user_id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def user_has_role(user: models.User, role: RoleEnum) -> bool:
    """Проверяет, есть ли у пользователя указанная роль."""
    return any(r.role_id == role for r in user.roles)

def user_has_any_role(user: models.User, *roles: RoleEnum) -> bool:
    """Проверяет наличие хотя бы одной роли из списка."""
    return not {r.role_id for r in user.roles}.isdisjoint(roles)

def require_any_role(*roles: str):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if not user_has_any_role(current_user, *roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return role_checker

@wraps(func)
def require_role(role: str):
    return require_any_role(role)