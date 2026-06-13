from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, model_validator

class QuestionOut(BaseModel):
    question_id: int
    question_text: str
    active: bool
    sort_order: int
    questions_type_id: int
    validator_type_id: int = 1
    type_of_thinking_id: Optional[int] = None
    focus: Optional[str] = None
    clarification_1: Optional[str] = None
    clarification_2: Optional[str] = None
    key_indicators: Optional[str] = None
    proof: Optional[str] = None
    interpretation_template: Optional[str] = None
    class Config: from_attributes = True

    @model_validator(mode='after')
    def validate_q38_fields(self):
        if self.questions_type_id == 2:
            required = ['type_of_thinking', 'focus', 'clarification_1', 'clarification_2',
                        'key_indicators', 'proof', 'interpretation_template']
            missing = [f for f in required if getattr(self, f) is None]
            if missing:
                raise ValueError(f'For questions_type_id=2, fields {missing} are required')
        return self

class QuestionCreate(BaseModel):
    question_text: str
    active: bool = True
    sort_order: int
    questions_type_id: int = 2
    type_of_thinking_id: Optional[int] = None
    validator_type_id: int = 1
    focus: Optional[str] = None
    clarification_1: Optional[str] = None
    clarification_2: Optional[str] = None
    key_indicators: Optional[str] = None
    proof: Optional[str] = None
    interpretation_template: Optional[str] = None

    @model_validator(mode='after')
    def validate_q38_fields(self):
        if self.questions_type_id == 2:
            required = ['type_of_thinking', 'focus', 'clarification_1', 'clarification_2',
                        'key_indicators', 'proof', 'interpretation_template']
            missing = [f for f in required if getattr(self, f) is None]
            if missing:
                raise ValueError(f'For questions_type_id=2, fields {missing} are required')
        return self

class QuestionUpdate(BaseModel):
    active: Optional[bool] = None
    sort_order: Optional[int] = None
    questions_type_id: Optional[int] = None
    validator_type_id: Optional[int] = None
    type_of_thinking_id: Optional[int] = None
    focus: Optional[str] = None
    clarification_1: Optional[str] = None
    clarification_2: Optional[str] = None
    key_indicators: Optional[str] = None
    proof: Optional[str] = None
    interpretation_template: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_q38_fields(self):
        if self.questions_type_id == 2:
            required = ['type_of_thinking', 'focus', 'clarification_1', 'clarification_2',
                        'key_indicators', 'proof', 'interpretation_template']
            missing = [f for f in required if getattr(self, f) is None]
            if missing:
                raise ValueError(f'For questions_type_id=2, fields {missing} are required')
        return self
