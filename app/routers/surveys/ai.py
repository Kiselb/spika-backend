from openai import OpenAI
from http.client import HTTPException
from sqlalchemy.orm import Session
from app.config import MODEL_NAME, PROXY_API_API_KEY, PROXY_API_OPENAI_BASE_URL
from app.constants import SurveyStateEnum
from ... import models

def llm_response_to_conclusion(system: str, user: str = None) -> str:
    """Преобразует ответ от LLM в заключение для пользователя"""
    client = OpenAI(
        api_key=PROXY_API_API_KEY,
        base_url=PROXY_API_OPENAI_BASE_URL,
    )
    
    print("Клиент OpenAI инициализирован. Отправляем запрос к LLM...")

    messages = [{"role": "system", "content": system}]
    if user:
        messages.append({"role": "user", "content": user})

    chat_completion = client.chat.completions.create(
        model=MODEL_NAME, 
        messages=messages
    )
    
    print("Ответ от LLM получен. Обрабатываем результат...")
    
    response_content = chat_completion.choices[0].message.content.strip()
    print(f"Ответ от LLM: {response_content}")
    return response_content

def ai_conclusion_questions05(survey: models.Survey) -> str:
    """Заключение по первому блоку из 5 вопросов"""
    print(f"Генерируем заключение по первым 5 вопросам для опроса {survey.survey_id}")

    if survey.survey_state != SurveyStateEnum.INITIALIZED:
        raise HTTPException(status_code=400, detail="Survey is not in INITIALIZED state")

    print(f"Подготовка к обращению к LLM для опроса {survey.survey_id}. Состояние опроса: {survey.survey_state}. Запускаем функцию заключения.")

    system = f"""
    Ты — опытный психолог. Проводишь предварительную диагностику мышления. Ты проводишь анализ ответов на 5 вопросов,
    которые задаются человеку в начале опроса. Ты анализируешь ответы и выдаёшь заключение в соответствии с ПРАВИЛАМИ АНАЛИЗА. 
    Ты не ставишь диагнозы, не придумываешь факты о жизни, здоровье, психике, доходах, профессии, семье.
    Ты не даёшь медицинских/психиатрических рекомендаций.

    ОТВЕТЫ ПАЦИЕНТА НА 5 БАЗОВЫХ ВОПРОСОВ:
    Вопрос 1: Сколько хотите получать денег за месяц в рублях - Ответ: {survey.desired_salary_level}
    Вопрос 2: Сколько можете получать за месяц - Ответ: {survey.able_salary_level}
    Вопрос 3: Сколько достойны получать или достигать - Ответ: {survey.decent_salary_level}
    Вопрос 4: О чём мечтаете - Ответ: {survey.dreams}
    Вопрос 5: За какое время хотите достичь свою мечту - Ответ: {survey.dreams_point}

    ПРАВИЛА АНАЛИЗА:
    1. Сравни числовые значения в ответах на вопросы 1, 2, 3.
    Найди минимальное среди них (если все три числа есть) и произведи оценку:
    - Минимальное значение в ответе на вопрос 1 ("Хочу") означает, что "Нет мотивации или амбиции ниже возможностей"
    - Минимальное значение в ответе на вопрос 2 ("Могу") означает, что "Недостаток компетенций или ограничивающее мышление"
    - Минимальное значение в ответе на вопрос 3 ("Достоин") означает, что "Заниженная самооценка, неуверенность"

    2. Оцени Мечту (ответ на вопрос 4) + Срок исполнения мечты (ответ на вопрос 5):
    - Мечта показывает разрыв между текущей проблемой и желаемым будущим.
    - Болевая точка — что человек хочет исправить (выводи только из ответа, не выдумывай).
    - Если срок <= 1 года и мечта ресурсоёмкая (миллионы, переезд, бизнес), то "Риск выгорания, слишком короткий горизонт"
    - Если срок >= 10 лет и мечта реальна, то "Избегание действий, страх"
    - Если ответы нечисловые → отметить в анализе.

    ФОРМАТ ОТВЕТА:
    Формат ответа в виде строки:
    "Минимум: [Хочу/Могу/Достоин] → [вывод]. Мечта: [текст] за [срок]. Болевая точка: [что хочет исправить]. Рекомендация: [одна фраза, не медицинская]."
    """
    print("Отправляем запрос к LLM для генерации заключения по первым 5 вопросам...")
    conclusion = llm_response_to_conclusion(system)
    print("Заключение по первому блоку из 5 вопросов:", conclusion)

    return conclusion

def ai_conclusion_questions38(survey: models.Survey) -> str:
    """Заключение по второму блоку из 38 вопросов"""
    if survey.survey_state != SurveyStateEnum.ANALYZING:
        raise HTTPException(status_code=400, detail="Survey is not in ANALYZING state")
    
    # answers = db.query(models.UserAnswer).filter(
    #     models.UserAnswer.survey_id == survey.survey_id
    # ).all()
    conclusion = "Заключение по второму блоку из 38 вопросов: 38 ответов."
    # Удаляем старые связи
    #
    #thinking_type_ids = [1, 2]  # пример новых типов мышления, которые мы хотим сохранить
    #db.query(models.SurveyTypeOfThinking).filter(
    #    models.SurveyTypeOfThinking.survey_id == survey.survey_id
    #).delete()
    # Добавляем новые типы
    #for tid in thinking_type_ids:
    #    db.add(models.SurveyTypeOfThinking(survey_id=survey.survey_id, types_of_thinking_id=tid))
    #db.flush()  # применяем изменения, но не коммитим, чтобы оставить в транзакции

    return conclusion

def ai_conclusion_values(survey: models.Survey) -> str:
    """Заглушка для /Survey/Conclusion/Values"""
    if survey.survey_state != SurveyStateEnum.ANALYZING:
        raise HTTPException(status_code=400, detail="Survey is not in ANALYZING state")
    conclusion = "Ценностное заключение"
    return conclusion

