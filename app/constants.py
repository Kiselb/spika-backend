from enum import Enum

class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"

class SurveyStateEnum(str, Enum):
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
