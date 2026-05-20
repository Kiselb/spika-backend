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
    INITIALIZED = "ИНИЦИАЛИЗИРОВАН"
    PREPARED = "ПОДГОТОВЛЕН"
    IN_PROGRESS = "ВЫПОЛНЯЕТСЯ"
    ANALYZING = "АНАЛИЗИРУЕТСЯ"
    COMPLETED = "ЗАВЕРШЁН"

class RoleEnum(str, Enum):
    SUBJECT = "Испытуемый"
    ADMIN = "Admin"
    DEVELOPER = "Developer"
    EXPERT = "Специалист"

class ConclusionTypeEnum(str, Enum):
    QUESTIONS_05 = "Questions05"
    QUESTIONS_38 = "Questions38"
    VALUES = "Values"
