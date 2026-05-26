from enum import Enum

class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"

"""
Состояния опроса:
INITIALIZED ──(POST /Conclusion/Questions05)──> PREPARED
PREPARED ──(первый ответ)──> IN_PROGRESS
IN_PROGRESS ──(последний ответ)──> ANALYZING
ANALYZING ──(все три заключения + типы мышления)──> COMPLETED
"""
class SurveyStateEnum(str, Enum):
    # INITIALIZED = "ИНИЦИАЛИЗИРОВАН"
    # PREPARED = "ПОДГОТОВЛЕН"
    # IN_PROGRESS = "ВЫПОЛНЯЕТСЯ"
    # ANALYZING = "АНАЛИЗИРУЕТСЯ"
    # COMPLETED = "ЗАВЕРШЁН"
    CREATED = "CREATED"
    Q05_IN_PROGRESS = "Q05_IN_PROGRESS"
    Q05_COMPLETED = "Q05_COMPLETED"
    Q05_ANALYZED = "Q05_ANALYZED"
    Q38_IN_PROGRESS = "Q38_IN_PROGRESS"
    Q38_COMPLETED = "Q38_COMPLETED"
    Q38_ANALYZED = "Q38_ANALYZED"
    Q15_IN_PROGRESS = "Q15_IN_PROGRESS"
    Q15_COMPLETED = "Q15_COMPLETED"
    Q15_ANALYZED = "Q15_ANALYZED"
    COMPLETED = "COMPLETED"

class RoleEnum(str, Enum):
    SUBJECT = "Испытуемый"
    ADMIN = "Admin"
    DEVELOPER = "Developer"
    EXPERT = "Специалист"

class ConclusionTypeEnum(str, Enum):
    QUESTIONS_05 = "Questions05"
    QUESTIONS_38 = "Questions38"
    VALUES = "Values"

class PromptTypeEnum(str, Enum):
    AQ5 = "AQ5"
    AQ38 = "AQ38"
    EST = "EST"

class AnswerState:
    PREPARED = 1
    SKIPPED = 2
    COMPLETED = 3

class QuestionsTypes:
    Q05 = 1
    Q38 = 2
    Q15 = 3
    