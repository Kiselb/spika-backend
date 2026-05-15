from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator
from .survey import SurveyOut
from ..constants import GenderEnum, RoleEnum

class EducationTypeOut(BaseModel):
    education_type_id: int
    education_type_name: str
    class Config: from_attributes = True

class UserCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    position: Optional[str] = None
    education_id: Optional[int] = None
    email: Optional[EmailStr] = None
    telegram: str
    telegram_id: int
    date_of_birth: Optional[date] = None  # формат DD-MM-YYYY
    gender: Optional[GenderEnum] = None
    married: Optional[bool] = None
    children: Optional[bool] = None
    roles: Optional[List[RoleEnum]] = []

    @field_validator("roles")
    @classmethod
    def check_no_subject(cls, v):
        if v and RoleEnum.SUBJECT in v:
            raise ValueError("Cannot assign SUBJECT role")
        return v
    
    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_dob(cls, v):
        if v is None:
            return None
        if isinstance(v, date):  # на случай, если пришло уже готовое date
            return v
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%d-%m-%Y").date()
            except ValueError:
                raise ValueError("DateOfBirth must be in DD-MM-YYYY format")
        raise ValueError("Invalid type for date_of_birth")

class UserOut(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    position: Optional[str] = None
    education: Optional[EducationTypeOut] = None
    email: Optional[EmailStr] = None
    telegram: str
    date_of_birth: Optional[str] = None
    gender: Optional[GenderEnum] = None
    married: Optional[bool] = None
    children: Optional[bool] = None
    survey: Optional[SurveyOut] = None
    roles: Optional[List[RoleOut]] = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def format_dob(cls, v):
        if v is None:
            return v
        if isinstance(v, date):
            return v.strftime("%d-%m-%Y")
        return v

    model_config = {"from_attributes": True}

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    position: Optional[str] = None
    education_id: Optional[int] = None
    email: Optional[EmailStr] = None
    telegram: Optional[str] = None
    date_of_birth: Optional[date] = None  # DD-MM-YYYY
    gender: Optional[GenderEnum] = None
    married: Optional[bool] = None
    children: Optional[bool] = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_dob(cls, v):
        if v is None:
            return None
        if isinstance(v, date):              # на случай, если пришло уже date
            return v
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%d-%m-%Y").date()
            except ValueError:
                raise ValueError("DateOfBirth must be in DD-MM-YYYY format")
        raise ValueError("Invalid type for date_of_birth")
    
class RoleOut(BaseModel):
    role_id: int
    role_name: RoleEnum
    class Config: from_attributes = True

class UserRolesUpdate(BaseModel):
    roles: List[RoleEnum]

    @field_validator("roles")
    @classmethod
    def check_no_subject(cls, v):
        if RoleEnum.SUBJECT in v:
            raise ValueError("Cannot assign SUBJECT role")
        return v
