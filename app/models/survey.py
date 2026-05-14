from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
from ..constants import SurveyStateEnum

class Question(Base):
    __tablename__ = "Questions"
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    question_text = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False)

    type_of_thinking = Column(Integer, ForeignKey("TypesOfThinking.types_of_thinking_id"), nullable=False)
    focus = Column(Text, nullable=False)
    clarification_1 = Column(Text, nullable=False)
    clarification_2 = Column(Text, nullable=False)
    key_indicators = Column(Text, nullable=False)
    proof = Column(Text, nullable=False)
    interpretation_template = Column(Text, nullable=False)

    thinking_type = relationship("TypeOfThinking")

class UserAnswer(Base):
    __tablename__ = "SurveysAnswers" # "UsersAnswers"
    survey_id = Column(Integer, ForeignKey("Surveys.survey_id"), primary_key=True)
    question_id = Column(Integer, ForeignKey("Questions.question_id"), primary_key=True)
    answer_text = Column(Text, nullable=True)

class Survey(Base):
    __tablename__ = "Surveys"
    survey_id = Column(Integer, primary_key=True, autoincrement=True)
    survey_state = Column(String(32), nullable=False, default=SurveyStateEnum.PREPARED) # "ПОДГОТОВЛЕН"
    survey_start_date = Column(DateTime, nullable=False)
    survey_finish_date = Column(DateTime, nullable=True)
    #survey_conclusion = Column(Text, nullable=True)

    # Salary fields
    fact_salary_level = Column(Numeric(15, 2), nullable=True)
    desired_salary_level = Column(Numeric(15, 2), nullable=True)
    able_salary_level = Column(Numeric(15, 2), nullable=True)
    decent_salary_level = Column(Numeric(15, 2), nullable=True)
    dreams = Column(Text, nullable=True)
    dreams_point = Column(Integer, nullable=True)

    survey_conclusion_q05 = Column(Text, nullable=True)
    survey_conclusion_q38 = Column(Text, nullable=True)
    survey_conclusion_val = Column(Text, nullable=True)

    types_of_thinking = relationship("TypeOfThinking", secondary="SurveysTypesOfThinking")

class TypeOfThinking(Base):
    __tablename__ = "TypesOfThinking"
    types_of_thinking_id = Column(Integer, primary_key=True, autoincrement=True)
    types_of_thinking_name = Column(String(255), unique=True, nullable=False)

class SurveyTypeOfThinking(Base):
    __tablename__ = "SurveysTypesOfThinking"
    survey_id = Column(Integer, ForeignKey("Surveys.survey_id"), primary_key=True)
    types_of_thinking_id = Column(Integer, ForeignKey("TypesOfThinking.types_of_thinking_id"), primary_key=True)

class SurveyPrompt(Base):
    __tablename__ = "SurveyPrompts"
    survey_id = Column(Integer, ForeignKey("Surveys.survey_id"), primary_key=True)
    prompt_id = Column(Integer, ForeignKey("SystemPrompts.prompt_id"), primary_key=True)