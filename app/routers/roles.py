from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from .. import security

router = APIRouter(prefix="/Roles", tags=["Roles"])

@router.get("/", response_model=list[schemas.RoleOut])
def get_roles(db: Session = Depends(get_db), current_user: models.User = Depends(security.require_role("Admin"))):
    return db.query(models.Role).all()
