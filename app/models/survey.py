from sqlalchemy import Column, ForeignKeyConstraint, Index, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
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
    validator_type_id = Column(Integer, ForeignKey("QuestionsValidatorsTypes.validator_type_id"), nullable=False, default=1)

    type_of_thinking_id = Column(Integer, ForeignKey("TypesOfThinking.types_of_thinking_id"), nullable=True)
    focus = Column(Text, nullable=True)
    clarification_1 = Column(Text, nullable=True)
    clarification_2 = Column(Text, nullable=True)
    key_indicators = Column(Text, nullable=True)
    proof = Column(Text, nullable=True)
    interpretation_template = Column(Text, nullable=True)

    thinking_type = relationship("TypeOfThinking", foreign_keys=[type_of_thinking_id])
    question_type = relationship("QuestionsType")
    validator_type = relationship("QuestionsValidatorType")

    __table_args__ = (
        Index(
            'uq_questions_active_type_sort',
            'questions_type_id', 
            'sort_order',
            unique=True,
            postgresql_where=(active == True)
        ),
    )

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
    conclusion_id = Column(Integer, ForeignKey("SurveysAnswersConclusions.conclusion_id"), nullable=True)
    conclusion_text = Column(Text, nullable=True)
    conclusion = relationship("SurveyAnswersConclusion", foreign_keys=[conclusion_id])
    survey = relationship("Survey", back_populates="answers")
    question = relationship("Question")   # связь для получения текста вопроса и других полей
    answer_state = relationship("SurveysAnswersState")  # связь для получения названия состояния ответа

class SurveysState(Base):
    __tablename__ = "SurveysStates"
    survey_state_id = Column(Integer, primary_key=True, nullable=False)
    survey_state_name = Column(String(255), unique=True, nullable=False)

class Survey(Base):
    __tablename__ = "Surveys"
    survey_id = Column(Integer, primary_key=True, autoincrement=True)
    survey_state_id = Column(
        Integer,
        ForeignKey("SurveysStates.survey_state_id"),
        nullable=False,
        default=1   # CREATED
    )
    survey_start_date = Column(DateTime, nullable=False)
    survey_finish_date = Column(DateTime, nullable=True)

    # Salary fields
    fact_salary_level = Column(Numeric(15, 2), nullable=True)
    desired_salary_level = Column(Numeric(15, 2), nullable=True)
    able_salary_level = Column(Numeric(15, 2), nullable=True)
    decent_salary_level = Column(Numeric(15, 2), nullable=True)
    dreams = Column(Text, nullable=True)
    dreams_point = Column(Text, nullable=True)

    survey_conclusion_q05 = Column(Text, nullable=True)
    survey_conclusion_q38 = Column(Text, nullable=True)
    survey_conclusion_q15 = Column(Text, nullable=True)

    survey_state = relationship("SurveysState")
    answers = relationship("UserAnswer", back_populates="survey", lazy="select")

class TypeOfThinking(Base):
    __tablename__ = "TypesOfThinking"
    types_of_thinking_id = Column(Integer, primary_key=True, autoincrement=True)
    types_of_thinking_name = Column(String(255), unique=True, nullable=False)
    definition = Column(Text, nullable=False)

class SurveyPrompt(Base):
    __tablename__ = "SurveyPrompts"
    survey_id = Column(Integer, ForeignKey("Surveys.survey_id"), primary_key=True)
    prompt_id = Column(Integer, ForeignKey("SystemPrompts.prompt_id"), primary_key=True)

class QuestionsType(Base):
    __tablename__ = "QuestionsTypes"
    questions_type_id = Column(Integer, primary_key=True, autoincrement=True)
    questions_type_name = Column(String(255), unique=True, nullable=False)

class QuestionsValidatorType(Base):
    __tablename__ = "QuestionsValidatorsTypes"
    validator_type_id = Column(Integer, primary_key=True, nullable=False)  # без autoincrement
    validator_type_name = Column(String(255), unique=True, nullable=False)

class SurveyAnswersConclusion(Base):
    __tablename__ = "SurveysAnswersConclusions"
    conclusion_id = Column(Integer, primary_key=True)
    conclusion_name = Column(String(255), unique=True, nullable=False)
