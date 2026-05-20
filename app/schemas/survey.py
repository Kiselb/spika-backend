from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator
from ..constants import SurveyStateEnum

class QAItem(BaseModel):
    question_id: int
    question: str
    answer: Optional[str] = None

class SurveyOut(BaseModel):
    survey_id: int
    survey_state: SurveyStateEnum
    start_date: str
    finish_date: Optional[str]
    fact_salary_level: Optional[float] = None
    desired_salary_level: Optional[float] = None
    able_salary_level: Optional[float] = None
    decent_salary_level: Optional[float] = None
    dreams: Optional[str] = None
    dreams_point: Optional[int] = None
    qa: List[QAItem]
    types_of_thinking: Optional[List[TypeOfThinkingOut]] = None
    survey_conclusion_q05: Optional[str] = None
    survey_conclusion_q38: Optional[str] = None
    survey_conclusion_val: Optional[str] = None

    @field_validator("start_date", "finish_date", mode="before")
    @classmethod
    def format_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.strftime("%d-%m-%Y %H:%M")
        return v

    model_config = {"from_attributes": True}

class SurveyAnswerRequest(BaseModel):
    answer_text: str

class TypesOfThinkingRequest(BaseModel):
    types_of_thinking: List[int]

class SalaryDreamsUpdate(BaseModel):
    fact_salary_level: float
    desired_salary_level: float
    able_salary_level: float
    decent_salary_level: float
    dreams: str
    dreams_point: str

class TypeOfThinkingOut(BaseModel):
    types_of_thinking_id: int
    types_of_thinking_name: str
    class Config: from_attributes = True

class TypeOfThinkingCreate(BaseModel):
    types_of_thinking_name: str