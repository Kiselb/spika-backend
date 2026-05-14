from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

class PromptOut(BaseModel):
    prompt_id: int
    prompt_type_id: int
    prompt_text: str
    class Config: from_attributes = True

class PromptCreate(BaseModel):
    prompt_type_id: int
    prompt_text: str

class PromptUpdate(BaseModel):
    prompt_type_id: Optional[int] = None
    prompt_text: Optional[str] = None

