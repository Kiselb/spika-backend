from __future__ import annotations
from pydantic import BaseModel

class EducationTypeOut(BaseModel):
    education_type_id: int
    education_type_name: str
    class Config: from_attributes = True

class EducationTypeCreate(BaseModel):
    education_type_name: str