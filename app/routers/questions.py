from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/Questions", tags=["Questions"])

@router.get("/", response_model=List[schemas.QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    return db.query(models.Question).all()

@router.post("/", response_model=schemas.QuestionOut, status_code=201)
def create_question(q: schemas.QuestionCreate, db: Session = Depends(get_db)):
    db_q = models.Question(**q.dict())
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q
