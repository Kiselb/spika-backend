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
    

    #if survey.survey_state != SurveyStateEnum.ANALYZING:
    #    raise HTTPException(status_code=400, detail="Survey is not in ANALYZING state")
    
    # answers = db.query(models.UserAnswer).filter(
    #     models.UserAnswer.survey_id == survey.survey_id
    # ).all()
    counter = 0
    conclusion = ""
    types_of_thinking = []
    for answer in survey.answers:
        print(f"""
              answer.question: {answer.question.question_text},
              answer.answer_text: {answer.answer_text}
              type of thinking: {answer.question.thinking_type.types_of_thinking_name}
              focus: {answer.question.focus}
              clarification1: {answer.question.clarification_1}
              clarification2: {answer.question.clarification_2}
              key_indicator: {answer.question.key_indicators}
              proof: {answer.question.proof}
              template: {answer.question.interpretation_template}""")
        system=f"""
        Ты — опытный психолог. Проводишь диагностику типов мышления. Ты проводишь анализ ответа пользователя на 
        вопрос, позволяющий определить наличие указанного типа мышления у пользователя.
        Ты не ставишь диагнозы, не придумываешь факты о жизни, здоровье, психике, доходах, профессии, семье.
        Ты не даёшь медицинских/психиатрических рекомендаций.

        БАЗОВЫЕ ДАННЫЕ:
        Была произведена базовая диагностика пользователя. Пользователь ответил на следущие вопросы:
        Вопрос 1: Сколько хотите получать денег за месяц в рублях? Ответ пользователя на вопрос 1: {survey.desired_salary_level}.
        Вопрос 2: Сколько можете получать за месяц? Ответ пользователя на вопрос 2: {survey.able_salary_level}.
        Вопрос 3: Сколько достойны получать или достигать? Ответ пользователя на вопрос 3: {survey.decent_salary_level}.
        Вопрос 4: О чём мечтаете? Ответ пользователя на вопрос 4: {survey.dreams}.
        Вопрос 5: За какое время хотите достичь свою мечту? Ответ пользователя на вопрос 5: {survey.dreams_point}.
        Заключение эксперта по ответам на указанные 5 вопросов: {survey.survey_conclusion_q05}.

        ВОПРОС:
        Был задан следующий вопрос: {answer.question.question_text} на определение следующего типа мышления: {answer.question.thinking_type.types_of_thinking_name}.
        Следует учитывать следующие параметры вопроса:
        - Акцентирующий вопрос, применительно к заданному вопросу: {answer.question.focus};
        - Уточняющий вопрос 1, применительно к заданному вопросу: {answer.question.clarification_1};
        - Уточняющий вопрос 2, применительно к заданному вопросу: {answer.question.clarification_2};
        - Ключевой индикатор, помогающий интерпретировать ответ пользователя: {answer.question.key_indicators};
        - Доказательства, помогающие определить наличие типа мышления: {answer.question.proof};
        - Шаблон интерпретации типа мышления: {answer.question.interpretation_template}.

        ОТВЕТ ПОЛЬЗОВАТЕЛЯ:
        На вопрос от пользователя был получен следующий ответ: {answer.answer_text}.

        ФОРМАТ ОТВЕТА:
        Отвечай только Да или Нет. Да - означает, что заданный тип мышления есть у пользователя.
        Нет - означает, что заданный тип мышления отсутствует у пользователя.
        """

        counter += 1
        print("Отправляем запрос к LLM для генерации заключения по вопросу {counter} из 38")
        answer_conclusion = llm_response_to_conclusion(system)
        print(f"Заключение по вопросу {counter} из 38:", answer_conclusion)
        if answer_conclusion.upper() not in ("Да".upper(), "Нет".upper()):
            print(f"Ответ LLM не распознан как 'Да' или 'Нет': {answer_conclusion}. Считаем ответ 'Нет' по умолчанию.")
            answer_conclusion = "Нет"
        
        if answer_conclusion.upper() == "Нет".upper():
            print(f"LLM определил отсутствие типа мышления для вопроса {counter}.")
            types_of_thinking.append(answer.question.thinking_type.types_of_thinking_id)
        conclusion += answer_conclusion
        conclusion += " - "  # разделитель между ответами на разные вопросы
    
    print("Заключение по вопросам:", conclusion, "Типы мышления, определённые как отсутствующие:", types_of_thinking)
    
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

    return conclusion, types_of_thinking

def ai_conclusion_values(survey: models.Survey) -> str:
    """Заглушка для /Survey/Conclusion/Values"""
    if survey.survey_state != SurveyStateEnum.ANALYZING:
        raise HTTPException(status_code=400, detail="Survey is not in ANALYZING state")
    conclusion = "Ценностное заключение"
    return conclusion

def ai_reformulate_question(question: str) -> str:
    """
    Переформулирует вопрос для лучшего понимания пользователем.
    Возвращает переформулированный текст вопроса.
    """
    client = OpenAI(
        api_key=PROXY_API_API_KEY,
        base_url=PROXY_API_OPENAI_BASE_URL,
    )

    system = (
        "Ты — ассистент, который помогает переформулировать сложные вопросы "
        "психологического опроса в более простые и понятные формулировки. "
        "Сохраняй исходный смысл, но делай вопрос дружелюбнее и яснее. "
        "Не добавляй новую информацию и не меняй тему."
    )
    user = f"Переформулируй этот вопрос: {question}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages
    )

    response_content = chat_completion.choices[0].message.content.strip()
    print(f"Переформулированный вопрос: {response_content}")
    return response_content