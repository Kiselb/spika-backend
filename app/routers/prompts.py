from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.routers.utils import get_latest_prompt_by_type
from ..database import get_db
from .. import models, schemas, security
from ..constants import PromptTypeEnum, RoleEnum

router = APIRouter(prefix="/Prompts", tags=["Prompts"])

def get_prompt_type_id(db: Session, prompt_type: PromptTypeEnum) -> int:
    """Возвращает prompt_type_id по названию типа, или 404."""
    ptype = db.query(models.SystemPromptType).filter(
        models.SystemPromptType.prompt_name == prompt_type.value
    ).first()
    if not ptype:
        raise HTTPException(status_code=404, detail=f"Prompt type '{prompt_type.value}' not found")
    return ptype.prompt_type_id

@router.get(
    "",
    response_model=List[schemas.PromptOut],
    description="Получить список всех промптов.",
    summary="Список промптов"
)
def get_prompts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER))
):
    return db.query(models.SystemPrompt).all()

@router.get(
    "/{prompt_type}",
    response_model=schemas.PromptOut,
    description="Получить последний промпт заданного типа.",
    summary="Получить последний промпт заданного типа (по имени типа, например AQ5)."
)
def get_prompt_by_type(
    prompt_type: PromptTypeEnum,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER))
):
    """Получить последний промпт заданного типа (по имени типа, например AQ5)."""
    type_id = get_prompt_type_id(db, prompt_type)
    prompt = get_latest_prompt_by_type(db, type_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="No prompt found for this type")
    return prompt

@router.post(
    "",
    response_model=schemas.PromptOut,
    status_code=201,
    description="Создать новый промпт.",
    summary="Создать промпт"
)
def create_prompt(
    prompt_data: schemas.PromptCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER))
):
    type_id = get_prompt_type_id(db, prompt_data.prompt_type)
    prompt = models.SystemPrompt(
        prompt_type_id=type_id,
        prompt_text=prompt_data.prompt_text
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

@router.put(
    "/{prompt_id}",
    response_model=schemas.PromptOut,
    description="Обновить существующий промпт.",
    summary="Обновить промпт"
)
def update_prompt(
    prompt_id: int,
    prompt_data: schemas.PromptUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER))
):
    prompt = db.query(models.SystemPrompt).filter(
        models.SystemPrompt.prompt_id == prompt_id
    ).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if prompt_data.prompt_type is not None:
        type_id = get_prompt_type_id(db, prompt_data.prompt_type)
        prompt.prompt_type_id = type_id
    if prompt_data.prompt_text is not None:
        prompt.prompt_text = prompt_data.prompt_text

    db.commit()
    db.refresh(prompt)
    return prompt
