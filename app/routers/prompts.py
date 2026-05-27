from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.routers.utils import get_latest_prompt_by_type, get_prompt_type_id
from ..database import get_db
from .. import models, schemas, security
from ..constants import PromptTypeEnum, RoleEnum

router = APIRouter(prefix="/Prompts", tags=["Prompts"])

@router.get(
    "",
    response_model=List[schemas.PromptOut],
    description="Получить список последних (активных) промптов каждого типа.",
    summary="Список активных промптов"
)
def get_prompts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.require_any_role(RoleEnum.DEVELOPER))
):
    # Подзапрос: для каждого prompt_type_id берём максимальный prompt_id
    subq = (
        db.query(
            models.SystemPrompt.prompt_type_id,
            func.max(models.SystemPrompt.prompt_id).label("max_id")
        )
        .group_by(models.SystemPrompt.prompt_type_id)
        .subquery()
    )

    # Выбираем сами записи промптов с максимальными ID для каждого типа
    latest_prompts = (
        db.query(models.SystemPrompt)
        .join(
            subq,
            (models.SystemPrompt.prompt_type_id == subq.c.prompt_type_id) & # можно убрать, оставлено для удобства чтения
            (models.SystemPrompt.prompt_id == subq.c.max_id)
        )
        .all()
    )
    return latest_prompts

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
