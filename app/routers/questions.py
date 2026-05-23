from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from .. import security
from ..constants import RoleEnum

router = APIRouter(prefix="/Questions", tags=["Questions"])

@router.get("/", response_model=List[schemas.QuestionOut])
def list_questions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.EXPERT, RoleEnum.DEVELOPER)),
    description="Получить список всех вопросов. Доступно для EXPERT и DEVELOPER.",
    summary="Список вопросов. Доступно для EXPERT и DEVELOPER."
):
    return db.query(models.Question).all()

@router.post("/", response_model=schemas.QuestionOut, status_code=201)
def create_question(
    q: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.EXPERT, RoleEnum.DEVELOPER)),
    description="Создать новый вопрос. Доступно для EXPERT и DEVELOPER.",
    summary="Создать новый вопрос. Доступно для EXPERT и DEVELOPER."
):
    db_q = models.Question(**q.dict())
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q

@router.put("/{question_id}", response_model=schemas.QuestionOut)
def update_question(
    question_id: int, 
    question_data: schemas.QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.EXPERT, RoleEnum.DEVELOPER)),
    description="Обновить существующий вопрос. Доступно для EXPERT и DEVELOPER.",
    summary="Обновить существующий вопрос. Доступно для EXPERT и DEVELOPER."   
):
    question = db.query(models.Question).filter(models.Question.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    for field, value in question_data.dict(exclude_unset=True).items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question