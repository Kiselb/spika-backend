from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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
        print(f'token: {token} secret: {SECRET_KEY} algorithm: {ALGORITHM} expire: {ACCESS_TOKEN_EXPIRE_MINUTES}')
        token_test = jwt.encode(claims={"sub": str(2)}, key=SECRET_KEY, algorithm=ALGORITHM)
        payload = jwt.decode(token=token_test, key=SECRET_KEY, algorithms=ALGORITHM)
        user_id: str = payload.get("sub")
        if user_id is None:
            print("""payload.get("sub") is None""")
            raise credentials_exception
    except JWTError:
        print("""JWTError""")
        raise credentials_exception
    print(f'user_id: {user_id}')
    user = db.query(models.User).filter(models.User.user_id == int(user_id)).first()
    if user is None:
        print("""user is None""")
        raise credentials_exception
    return user

def require_role(role_name: str):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        print(f'current_user.roles: {current_user.roles}')
        if not any(role.role_name == role_name for role in current_user.roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return role_checker

def require_any_role(*roles: str):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        user_roles = {role.role_name for role in current_user.roles}
        print(f"user_roles: {user_roles}")
        if not user_roles.intersection(roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return role_checker
