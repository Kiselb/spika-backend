from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/TypesOfThinking", tags=["TypesOfThinking"])

@router.get("/", response_model=List[schemas.TypeOfThinkingOut])
def list_thinking(db: Session = Depends(get_db)):
    return db.query(models.TypeOfThinking).all()

@router.post("/", response_model=schemas.TypeOfThinkingOut, status_code=201)
def create_thinking(tt: schemas.TypeOfThinkingCreate, db: Session = Depends(get_db)):
    db_tt = models.TypeOfThinking(**tt.dict())
    db.add(db_tt)
    db.commit()
    db.refresh(db_tt)
    return db_tt
