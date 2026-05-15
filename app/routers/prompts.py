from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, security
from ..constants import RoleEnum

router = APIRouter(prefix="/Prompts", tags=["Prompts"])

@router.get("", response_model=List[schemas.PromptOut])
def get_prompts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER))
):
    return db.query(models.SystemPrompt).all()

@router.post("", response_model=schemas.PromptOut, status_code=201)
def create_prompt(
    prompt_data: schemas.PromptCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER))
):
    prompt = models.SystemPrompt(**prompt_data.dict())
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

@router.put("/{prompt_id}", response_model=schemas.PromptOut)
def update_prompt(
    prompt_id: int,
    prompt_data: schemas.PromptUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER))
):
    prompt = db.query(models.SystemPrompt).filter(models.SystemPrompt.prompt_id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    for field, value in prompt_data.dict(exclude_unset=True).items():
        setattr(prompt, field, value)
    db.commit()
    db.refresh(prompt)
    return prompt
