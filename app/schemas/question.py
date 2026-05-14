from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

class QuestionOut(BaseModel):
    question_id: int
    question_text: str
    active: bool
    sort_order: int

    type_of_thinking: int
    focus: str
    clarification_1: str
    clarification_2: str
    key_indicators: str
    proof: str
    interpretation_template: str

    class Config: from_attributes = True

class QuestionCreate(BaseModel):
    question_text: str
    active: bool = True
    sort_order: int

    type_of_thinking: int
    focus: str
    clarification_1: str
    clarification_2: str
    key_indicators: str
    proof: str
    interpretation_template: str

class QuestionUpdate(BaseModel):
    active: Optional[bool] = None
    sort_order: Optional[int] = None

    type_of_thinking: Optional[int] = None
    focus: Optional[str] = None
    clarification_1: Optional[str] = None
    clarification_2: Optional[str] = None
    key_indicators: Optional[str] = None
    proof: Optional[str] = None
    interpretation_template: Optional[str] = None

