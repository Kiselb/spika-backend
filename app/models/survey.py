from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
from ..constants import AnswerState, QuestionsTypes, SurveyStateEnum

class Question(Base):
    __tablename__ = "Questions"
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    question_text = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False)
    questions_type_id = Column(Integer, ForeignKey("QuestionsTypes.questions_type_id"), nullable=False, default=QuestionsTypes.Q38)

    type_of_thinking = Column(Integer, ForeignKey("TypesOfThinking.types_of_thinking_id"), nullable=True)
    focus = Column(Text, nullable=True)
    clarification_1 = Column(Text, nullable=True)
    clarification_2 = Column(Text, nullable=True)
    key_indicators = Column(Text, nullable=True)
    proof = Column(Text, nullable=True)
    interpretation_template = Column(Text, nullable=True)

    thinking_type = relationship("TypeOfThinking")
    question_type = relationship("QuestionsType")

class SurveysAnswersState(Base):
    __tablename__ = "SurveysAnswersStates"
    answer_state_id = Column(Integer, primary_key=True, autoincrement=True)
    answer_state_name = Column(String(50), unique=True, nullable=False)

class UserAnswer(Base):
    __tablename__ = "SurveysAnswers" # "UsersAnswers"
    survey_id = Column(Integer, ForeignKey("Surveys.survey_id"), primary_key=True)
    question_id = Column(Integer, ForeignKey("Questions.question_id"), primary_key=True)
    answer_text = Column(Text, nullable=True)
    answer_state_id = Column(
        Integer,
        ForeignKey("SurveysAnswersStates.answer_state_id"),
        nullable=False,
        default=AnswerState.PREPARED  # 1 = ПОДГОТОВЛЕН
    )
    reformulated_text = Column(Text, nullable=True)

    survey = relationship("Survey", back_populates="answers")
    question = relationship("Question")   # связь для получения текста вопроса и других полей
    answer_state = relationship("SurveysAnswersState")  # связь для получения названия состояния ответа

class Survey(Base):
    __tablename__ = "Surveys"
    survey_id = Column(Integer, primary_key=True, autoincrement=True)
    survey_state = Column(String(32), nullable=False, default=SurveyStateEnum.CREATED)
    survey_start_date = Column(DateTime, nullable=False)
    survey_finish_date = Column(DateTime, nullable=True)
    #survey_conclusion = Column(Text, nullable=True)

    # Salary fields
    fact_salary_level = Column(Numeric(15, 2), nullable=True)
    desired_salary_level = Column(Numeric(15, 2), nullable=True)
    able_salary_level = Column(Numeric(15, 2), nullable=True)
    decent_salary_level = Column(Numeric(15, 2), nullable=True)
    dreams = Column(Text, nullable=True)
    dreams_point = Column(Text, nullable=True)

    survey_conclusion_q05 = Column(Text, nullable=True)
    survey_conclusion_q38 = Column(Text, nullable=True)
    survey_conclusion_val = Column(Text, nullable=True)

    types_of_thinking = relationship("TypeOfThinking", secondary="SurveysTypesOfThinking")
    answers = relationship("UserAnswer", back_populates="survey", lazy="select")

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

class QuestionsType(Base):
    __tablename__ = "QuestionsTypes"
    questions_type_id = Column(Integer, primary_key=True, autoincrement=True)
    questions_type_name = Column(String(255), unique=True, nullable=False)
