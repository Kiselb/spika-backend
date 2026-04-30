from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/EducationTypes", tags=["EducationTypes"])

@router.get("/", response_model=List[schemas.EducationTypeOut])
def list_education(db: Session = Depends(get_db)):
    return db.query(models.EducationType).all()

@router.post("/", response_model=schemas.EducationTypeOut, status_code=201)
def create_education(edu: schemas.EducationTypeCreate, db: Session = Depends(get_db)):
    db_edu = models.EducationType(**edu.dict())
    db.add(db_edu)
    db.commit()
    db.refresh(db_edu)
    return db_edu
