from enum import Enum

class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"

"""
Состояния опроса:
CREATED
(первый ответ) ──> Q05_IN_PROGRESS (последний ответ) ──> Q05_COMPLETED (POST /Conclusion/Questions05)──> Q05_ANALYZED
(первый ответ) ──> Q38_IN_PROGRESS (последний ответ) ──> Q38_COMPLETED (POST /Conclusion/Questions38)──> Q38_ANALYZED
(первый ответ) ──> Q15_IN_PROGRESS (последний ответ) ──> Q15_COMPLETED (POST /Conclusion/Questions15)──> Q15_ANALYZED
COMPLETED
"""
class SurveyStateEnum(str, Enum):
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

class PromptTypeEnum(str, Enum):
    AQ05 = "AQ05"
    AQ38 = "AQ38"
    AQ15 = "AQ15"
    QREF = "QREF"
    QTRA = "QTRA"

class AnswerState:
    PREPARED = 1
    SKIPPED = 2
    COMPLETED = 3

class QuestionsTypes:
    Q05 = 1
    Q38 = 2
    Q15 = 3
    