from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from ..database import Base

class EducationType(Base):
    __tablename__ = "EducationTypes"
    education_type_id = Column(Integer, primary_key=True, autoincrement=True)
    education_type_name = Column(String(255), unique=True, nullable=False)

class User(Base):
    __tablename__ = "Users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("Surveys.survey_id"), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    middle_name = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    education_id = Column(Integer, ForeignKey("EducationTypes.education_type_id"), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    telegram = Column(String(255), unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(6), nullable=True)  # "Male" / "Female"
    married = Column(Boolean, nullable=True)
    children = Column(Boolean, nullable=True)

    education = relationship("EducationType")
    survey = relationship("Survey", foreign_keys=[survey_id])
    roles = relationship("Role", secondary="UsersRoles", back_populates="users") # roles = relationship("Role", secondary="UsersRoles", backref="users")

    telegram_id = Column(BigInteger, unique=True, nullable=False)
