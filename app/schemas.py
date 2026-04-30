from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class GenderEnum(str, Enum):
    male = "Male"
    female = "Female"

class SurveyStateEnum(str, Enum):
    prepared = "ПОДГОТОВЛЕН"
    in_progress = "ВЫПОЛНЯЕТСЯ"
    analyzing = "АНАЛИЗИРУЕТСЯ"
    completed = "ЗАВЕРШЁН"

# ----- Education -----
class EducationTypeOut(BaseModel):
    education_type_id: int
    education_type_name: str
    class Config: from_attributes = True

class EducationTypeCreate(BaseModel):
    education_type_name: str

# ----- Names composite -----
class NamesOut(BaseModel):
    First: str
    Last: str
    Middle: Optional[str] = None

class NamesIn(BaseModel):
    First: str
    Last: str
    Middle: Optional[str] = None

# ----- User -----
class UserCreate(BaseModel):
    Names: NamesIn
    Position: Optional[str] = None
    Education: Optional[int] = Field(None, alias="Education")  # education_id
    Email: EmailStr
    Telegram: Optional[str] = None
    DateOfBirth: str  # формат DD-MM-YYYY
    Gender: GenderEnum
    Married: Optional[bool] = None
    Children: Optional[bool] = None

    @validator("DateOfBirth")
    def validate_dob(cls, v):
        try:
            return datetime.strptime(v, "%d-%m-%Y").date()
        except ValueError:
            raise ValueError("DateOfBirth must be in DD-MM-YYYY format")

class UserOut(BaseModel):
    Names: NamesOut
    Position: Optional[str] = None
    Education: Optional[int] = None  # EducationID
    Email: str
    Telegram: Optional[str] = None
    DateOfBirth: str
    Gender: str
    Married: Optional[bool] = None
    Children: Optional[bool] = None
    Survey: Optional[SurveyOut] = None

    @validator("DateOfBirth", pre=True)
    def format_dob(cls, v):
        if isinstance(v, date):
            return v.strftime("%d-%m-%Y")
        return v

    class Config: from_attributes = True

# ----- QA -----
class QAItem(BaseModel):
    Question: str
    Answer: Optional[str] = None

# ----- Survey -----
class SurveyOut(BaseModel):
    SurveyID: int = Field(alias="SurveyID")
    SurveyState: str = Field(alias="SurveyState")
    StartDate: str = Field(alias="StartDate")
    FinishDate: Optional[str] = Field(alias="FinishDate")
    FactSalaryLevel: Optional[float] = None
    DesiredSalaryLevel: Optional[float] = None
    AbleSalaryLevel: Optional[float] = None
    DecentSalaryLevel: Optional[float] = None
    Dreams: Optional[str] = None
    DreamsPoint: Optional[int] = None
    QA: List[QAItem] = Field(alias="QA", default_factory=list)
    TypesOfThinking: Optional[List[int]] = None
    SurveyConclusion: Optional[str] = None

    @validator("StartDate", "FinishDate", pre=True)
    def format_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.strftime("%d-%m-%Y %H:%M")
        return v

    class Config: from_attributes = True

class SurveyCreateResponse(BaseModel):
    SurveyID: int

class SurveyAnswerRequest(BaseModel):
    Answer: str

class ConclusionRequest(BaseModel):
    Conclusion: str

class TypesOfThinkingRequest(BaseModel):
    TypesOfThinking: List[int]

class SalaryDreamsUpdate(BaseModel):
    FactSalaryLevel: Optional[float] = None
    DesiredSalaryLevel: Optional[float] = None
    AbleSalaryLevel: Optional[float] = None
    DecentSalaryLevel: Optional[float] = None
    Dreams: Optional[str] = None
    DreamsPoint: Optional[int] = None

# ----- Questions -----
class QuestionOut(BaseModel):
    question_id: int
    question_text: str
    active: bool
    sort_order: int
    class Config: from_attributes = True

class QuestionCreate(BaseModel):
    question_text: str
    active: bool = True
    sort_order: int

# ----- Types of Thinking -----
class TypeOfThinkingOut(BaseModel):
    types_of_thinking_id: int
    types_of_thinking_name: str
    class Config: from_attributes = True

class TypeOfThinkingCreate(BaseModel):
    types_of_thinking_name: str
    