from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .database import get_db
from . import models
import os

# Настройки JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(role_name: str):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if not any(role.role_name == role_name for role in current_user.roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return role_checker

def require_any_role(*roles: str):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        user_roles = {role.role_name for role in current_user.roles}
        if not user_roles.intersection(roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return role_checker
