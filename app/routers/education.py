from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/EducationTypes", tags=["EducationTypes"])

@router.get(
    "/",
    response_model=List[schemas.EducationTypeOut],
    description="Получить список всех типов образования.",
    summary="Список типов образования")
def list_education(
    db: Session = Depends(get_db)
):
    return db.query(models.EducationType).all()
