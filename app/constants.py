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
class SurveyStateEnum(int, Enum):
    CREATED = 1
    Q05_IN_PROGRESS = 2
    Q05_COMPLETED = 3
    Q05_ANALYZED = 4
    Q38_IN_PROGRESS = 5
    Q38_COMPLETED = 6
    Q38_ANALYZED = 7
    Q15_IN_PROGRESS = 8
    Q15_COMPLETED = 9
    Q15_ANALYZED = 10
    COMPLETED = 11

class RoleEnum(int, Enum):
    SUBJECT = 1
    EXPERT = 2
    ADMIN = 3
    DEVELOPER = 4

class PromptTypeEnum(int, Enum):
    AQ05 = 1
    AQ38 = 2
    AQ15 = 3
    QREF = 4
    QTRA = 5
    MD2Q = 6
    MD2I = 7

class AnswerState(int, Enum):
    PREPARED = 1
    INPROGRESS = 2
    SKIPPED = 3
    COMPLETED = 4

class QuestionsTypes(int, Enum):
    Q05 = 1
    Q38 = 2
    Q15 = 3
