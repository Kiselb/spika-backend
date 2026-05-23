from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from app.constants import PromptTypeEnum

class PromptOut(BaseModel):
    prompt_id: int
    prompt_type_id: int
    prompt_text: str
    class Config: from_attributes = True

class PromptCreate(BaseModel):
    prompt_type_id: PromptTypeEnum
    prompt_text: str

class PromptUpdate(BaseModel):
    prompt_type_id: Optional[PromptTypeEnum] = None
    prompt_text: Optional[str] = None

