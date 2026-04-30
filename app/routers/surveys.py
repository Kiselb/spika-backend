from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/Survey", tags=["Surveys"])

def get_survey_or_404(survey_id: int, db: Session) -> models.Survey:
    survey = db.query(models.Survey).filter(models.Survey.survey_id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return survey

def build_qa(survey_id: int, db: Session) -> List[schemas.QAItem]:
    """Список вопросов-ответов для опроса, упорядоченный по SortOrder вопросов."""
    answers = db.query(models.UserAnswer).filter(models.UserAnswer.survey_id == survey_id).all()
    # Получаем активные вопросы в правильном порядке? В QA должны быть все вопросы, которые были добавлены.
    # Они соответствуют всем записям UserAnswers для этого опроса. Джойним с Questions для текста.
    qa_list = []
    for ans in answers:
        question = db.query(models.Question).filter(models.Question.question_id == ans.question_id).first()
        qa_list.append(schemas.QAItem(Question=question.question_text if question else "", Answer=ans.answer_text))
    # Сортируем по sort_order вопросов (если есть)
    # Лучше получить через запрос с джойном и сортировкой
    return qa_list

def build_qa_sorted(survey_id: int, db: Session) -> List[schemas.QAItem]:
    results = (
        db.query(models.UserAnswer.answer_text, models.Question.question_text, models.Question.sort_order)
        .join(models.Question, models.UserAnswer.question_id == models.Question.question_id)
        .filter(models.UserAnswer.survey_id == survey_id)
        .order_by(models.Question.sort_order)
        .all()
    )
    return [schemas.QAItem(Question=q_text, Answer=ans_text) for ans_text, q_text, _ in results]

def build_survey_out(survey: models.Survey, db: Session) -> schemas.SurveyOut:
    types_ids = None
    if survey.types_of_thinking:
        types_ids = [t.types_of_thinking_id for t in survey.types_of_thinking]
    return schemas.SurveyOut(
        SurveyID=survey.survey_id,
        SurveyState=survey.survey_state,
        StartDate=survey.survey_start_date,
        FinishDate=survey.survey_finish_date,
        FactSalaryLevel=float(survey.fact_salary_level) if survey.fact_salary_level else None,
        DesiredSalaryLevel=float(survey.desired_salary_level) if survey.desired_salary_level else None,
        AbleSalaryLevel=float(survey.able_salary_level) if survey.able_salary_level else None,
        DecentSalaryLevel=float(survey.decent_salary_level) if survey.decent_salary_level else None,
        Dreams=survey.dreams,
        DreamsPoint=survey.dreams_point,
        QA=build_qa_sorted(survey.survey_id, db),
        TypesOfThinking=types_ids,
        SurveyConclusion=survey.survey_conclusion
    )

def try_complete_survey(survey: models.Survey, db: Session):
    """Проверяет, можно ли перевести опрос в ЗАВЕРШЁН."""
    if survey.survey_conclusion and survey.types_of_thinking:
        survey.survey_state = "ЗАВЕРШЁН"
        db.commit()

# POST /Survey/{UserID}
@router.post("/{user_id}", response_model=schemas.SurveyCreateResponse)
def create_survey_for_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Если опрос уже есть, вернуть его ID
    if user.survey_id:
        return {"SurveyID": user.survey_id}

    # Создаём опрос
    survey = models.Survey(
        survey_state="ПОДГОТОВЛЕН",
        survey_start_date=datetime.now()
    )
    db.add(survey)
    db.flush()  # чтобы получить survey.survey_id
    # Копируем активные вопросы в UsersAnswers
    active_questions = db.query(models.Question).filter(models.Question.active == True).order_by(models.Question.sort_order).all()
    for q in active_questions:
        ua = models.UserAnswer(survey_id=survey.survey_id, question_id=q.question_id, answer_text=None)
        db.add(ua)
    # Связываем с пользователем
    user.survey_id = survey.survey_id
    db.commit()
    return {"SurveyID": survey.survey_id}

# GET /Survey/{UserID}
@router.get("/{user_id}", response_model=schemas.SurveyOut)
def get_survey_by_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user or not user.survey_id:
        raise HTTPException(status_code=404, detail="User or survey not found")
    survey = get_survey_or_404(user.survey_id, db)
    return build_survey_out(survey, db)

# POST /Survey/{SurveyID}/{QuestionID}
@router.post("/{survey_id}/{question_id}")
def answer_question(survey_id: int, question_id: int, answer_data: schemas.SurveyAnswerRequest, db: Session = Depends(get_db)):
    survey = get_survey_or_404(survey_id, db)
    # Проверить, что вопрос существует и принадлежит опросу (есть запись в UsersAnswers)
    ua = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.question_id == question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not found in this survey")
    # Записать ответ
    ua.answer_text = answer_data.Answer
    # Логика изменения состояния
    # Проверим, был ли это первый ответ
    answered_count = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.answer_text != None
    ).count()
    if answered_count == 1 and survey.survey_state == "ПОДГОТОВЛЕН":
        survey.survey_state = "ВЫПОЛНЯЕТСЯ"
    # Проверим, все ли вопросы отвечены
    total_questions = db.query(models.UserAnswer).filter(models.UserAnswer.survey_id == survey_id).count()
    if answered_count == total_questions:
        survey.survey_state = "АНАЛИЗИРУЕТСЯ"
        survey.survey_finish_date = datetime.now()
    db.commit()
    return {"status": "ok"}

# GET /Survey/{SurveyID}/{QuestionID}
@router.get("/{survey_id}/{question_id}")
def get_answer(survey_id: int, question_id: int, db: Session = Depends(get_db)):
    get_survey_or_404(survey_id, db)
    ua = db.query(models.UserAnswer).filter(
        models.UserAnswer.survey_id == survey_id,
        models.UserAnswer.question_id == question_id
    ).first()
    if not ua:
        raise HTTPException(status_code=404, detail="Question not found in this survey")
    return {"Answer": ua.answer_text}

# PUT /Survey/{SurveyID}/Conclusion
@router.put("/{survey_id}/Conclusion")
def set_conclusion(survey_id: int, conclusion: schemas.ConclusionRequest, db: Session = Depends(get_db)):
    survey = get_survey_or_404(survey_id, db)
    survey.survey_conclusion = conclusion.Conclusion
    db.commit()
    try_complete_survey(survey, db)
    return {"status": "ok"}

# GET /Survey/{SurveyID}/Conclusion
@router.get("/{survey_id}/Conclusion")
def get_conclusion(survey_id: int, db: Session = Depends(get_db)):
    survey = get_survey_or_404(survey_id, db)
    return {"Conclusion": survey.survey_conclusion}

# PUT /Survey/{SurveyID}/TypesOfThinking
@router.put("/{survey_id}/TypesOfThinking")
def set_types_of_thinking(survey_id: int, data: schemas.TypesOfThinkingRequest, db: Session = Depends(get_db)):
    survey = get_survey_or_404(survey_id, db)
    # Удалить старые записи
    db.query(models.SurveyTypeOfThinking).filter(models.SurveyTypeOfThinking.survey_id == survey_id).delete()
    # Проверить, что все указанные типы существуют
    types = db.query(models.TypeOfThinking).filter(models.TypeOfThinking.types_of_thinking_id.in_(data.TypesOfThinking)).all()
    if len(types) != len(data.TypesOfThinking):
        raise HTTPException(status_code=400, detail="One or more TypesOfThinking IDs are invalid")
    # Вставить новые записи
    for tid in data.TypesOfThinking:
        db.add(models.SurveyTypeOfThinking(survey_id=survey_id, types_of_thinking_id=tid))
    db.commit()
    # Обновить объект survey, чтобы relationship подтянул актуальные данные
    db.refresh(survey)
    try_complete_survey(survey, db)
    return {"status": "ok"}

# GET /Survey/{SurveyID}/TypesOfThinking
@router.get("/{survey_id}/TypesOfThinking")
def get_types_of_thinking(survey_id: int, db: Session = Depends(get_db)):
    survey = get_survey_or_404(survey_id, db)
    ids = [t.types_of_thinking_id for t in survey.types_of_thinking]
    return {"TypesOfThinking": ids}

# PUT /Survey/{SurveyID}/SalaryDreams (дополнительный эндпоинт)
@router.put("/{survey_id}/SalaryDreams")
def update_salary_dreams(survey_id: int, data: schemas.SalaryDreamsUpdate, db: Session = Depends(get_db)):
    survey = get_survey_or_404(survey_id, db)
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(survey, field, value)
    db.commit()
    return {"status": "ok"}
