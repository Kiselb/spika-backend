import json
import re

from openai import OpenAI
from http.client import HTTPException
from sqlalchemy.orm import Session
from app.config import MODEL_NAME, PROXY_API_API_KEY, PROXY_API_OPENAI_BASE_URL
from app.constants import PromptTypeEnum, QuestionsTypes, SurveyStateEnum
from app.routers.utils import get_user_answer_by_type_and_sort_order
from app.routers.utils import get_latest_prompt_by_type
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
    print(f"Подключение к LLM {MODEL_NAME} выполнено. Получаем ответ от LLM...")
    response_content = chat_completion.choices[0].message.content.strip()
    print(f"Ответ от LLM: {response_content}")
    
    return response_content

def ai_conclusion_questions05_fallback(survey: models.Survey) -> str:
    """Заключение по первому блоку из 5 вопросов"""
    print(f"Генерируем заключение по первым 5 вопросам для опроса {survey.survey_id}")
    print(f"Подготовка к обращению к LLM для опроса {survey.survey_id}. Состояние опроса: {survey.survey_state_id}. Запускаем функцию заключения.")

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

def ai_conclusion_questions05(survey: models.Survey, db: Session) -> str:
    prompt_record = get_latest_prompt_by_type(db, PromptTypeEnum.AQ05)
    if not prompt_record:
        raise HTTPException(status_code=404, detail=f"Prompt for {PromptTypeEnum.AQ05} not found")
    
    template = prompt_record.prompt_text

    values = {
        "survey_desired_salary_level": get_user_answer_by_type_and_sort_order(db, survey.survey_id, QuestionsTypes.Q05, 1).answer_text,
        "survey_able_salary_level": get_user_answer_by_type_and_sort_order(db, survey.survey_id, QuestionsTypes.Q05, 2).answer_text,
        "survey_decent_salary_level": get_user_answer_by_type_and_sort_order(db, survey.survey_id, QuestionsTypes.Q05, 3).answer_text,
        "survey_dreams": get_user_answer_by_type_and_sort_order(db, survey.survey_id, QuestionsTypes.Q05, 4).answer_text,
        "survey_dreams_point": get_user_answer_by_type_and_sort_order(db, survey.survey_id, QuestionsTypes.Q05, 5).answer_text,
    }
    print("Параметры для запроса к LLM:", values)
    system = template.format(**values)
    print("Отправляем запрос к LLM для генерации заключения по первому блоку из 5 вопросов...")
    conclusion = llm_response_to_conclusion(system)
    return conclusion

def ai_conclusion_questions38_fallback(survey: models.Survey) -> str:
    """Заключение по второму блоку из 38 вопросов"""
    

    #if survey.survey_state_id != SurveyStateEnum.ANALYZING:
    #    raise HTTPException(status_code=400, detail="Survey is not in ANALYZING state")
    
    # answers = db.query(models.UserAnswer).filter(
    #     models.UserAnswer.survey_id == survey.survey_id
    # ).all()
    counter = 0
    conclusion = ""
    types_of_thinking = []

    # Фильтруем только вопросы типа Q38, у которых есть thinking_type
    q38_answers = [
        ans for ans in survey.answers
        if ans.question.questions_type_id == 2 and ans.question.thinking_type is not None
    ]

    for answer in q38_answers:
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
        print(f"Отправляем запрос к LLM {MODEL_NAME} для генерации заключения по вопросу {counter} из 38")
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
    
    return conclusion, types_of_thinking

def has_key_in_template(template: str, key: str) -> bool:
    """Возвращает True, если ключ используется в строке шаблона."""
    # Ищет {key}, {key!r}, {key:формат} и т.п.
    return bool(re.search(rf'\{{\s*{re.escape(key)}\s*[!:]?[^}}]*\}}', template))

def ai_conclusion_questions38_single(survey: models.Survey, answer: models.UserAnswer, db: Session) -> str:
    """Заключение по одному вопросу из 38 вопросов"""
    prompt_record = get_latest_prompt_by_type(db, PromptTypeEnum.AQ38)
    if not prompt_record:
        raise HTTPException(status_code=404, detail=f"Prompt for {PromptTypeEnum.AQ38} not found")
    
    template = prompt_record.prompt_text

    result = [item.strip() for item in answer.question.key_indicators.split(";")]
    key_indicators = ";\n\t- ".join(result)
    key_indicators = "\t- " + key_indicators

    values = {}
    
    # Параметры базового опроса из 5 вопросов

    if has_key_in_template(template, "survey_desired_salary_level"):
        values["survey_desired_salary_level"] = survey.desired_salary_level
    if has_key_in_template(template, "survey_able_salary_level"):
        values["survey_able_salary_level"] = survey.able_salary_level
    if has_key_in_template(template, "survey_decent_salary_level"):
        values["survey_decent_salary_level"] = survey.decent_salary_level
    if has_key_in_template(template, "survey_dreams"):
        values["survey_dreams"] = survey.dreams
    if has_key_in_template(template, "survey_dreams_point"):
        values["survey_dreams_point"] = survey.dreams_point
    if has_key_in_template(template, "survey_survey_conclusion_q05"):
        values["survey_survey_conclusion_q05"] = survey.survey_conclusion_q05
        
    # Параметры вопроса из 38 вопросов

    if has_key_in_template(template, "thinking_type_definition"):
        values["thinking_type_definition"] = answer.question.thinking_type.definition
    if has_key_in_template(template, "answer_question_question_text"):
        values["answer_question_question_text"] = answer.question.question_text
    if has_key_in_template(template, "answer_answer_text"):    
        values["answer_answer_text"] = answer.answer_text
    if has_key_in_template(template, "answer_question_thinking_type_types_of_thinking_name"):
        values["answer_question_thinking_type_types_of_thinking_name"] = answer.question.thinking_type.types_of_thinking_name
    if has_key_in_template(template, "answer_question_focus"):
        values["answer_question_focus"] = answer.question.focus
    if has_key_in_template(template, "answer_question_clarification1"):
        values["answer_question_clarification1"] = answer.question.clarification_1
    if has_key_in_template(template, "answer_question_clarification2"):
        values["answer_question_clarification2"] = answer.question.clarification_2
    if has_key_in_template(template, "answer_question_key_indicators"):
        values["answer_question_key_indicators"] = key_indicators
    if has_key_in_template(template, "answer_question_proof"):
        values["answer_question_proof"] = answer.question.proof
    if has_key_in_template(template, "answer_question_interpretation_template"):
        values["answer_question_interpretation_template"] = answer.question.interpretation_template

    system = template.format(**values)
    print("System prompt: ========================================================================================")
    print(system)
    print("System prompt: ========================================================================================")

    print(f"Отправляем запрос к LLM {MODEL_NAME} для генерации заключения по вопросу {answer.question.question_text}")
    answer_conclusion = llm_response_to_conclusion(system)
    # if answer_conclusion.upper() not in ("Да".upper(), "Нет".upper(), "Условно присутствует".upper()):
    #     print(f"Ответ LLM не распознан как 'Да', 'Нет' или 'Условно присутствует': {answer_conclusion}. Считаем ответ 'Нет' по умолчанию.")
    #     answer_conclusion = "Нет*"
    
    return answer_conclusion

def ai_conclusion_questions38(survey: models.Survey, db: Session) -> str:
    """Заключение по второму блоку из 38 вопросов"""
    
    prompt_record = get_latest_prompt_by_type(db, PromptTypeEnum.S38R)
    if not prompt_record:
        raise HTTPException(status_code=404, detail=f"Prompt for {PromptTypeEnum.S38R} not found")    
    template = prompt_record.prompt_text
    
    q38_answers = [answer for answer in survey.answers if answer.question.questions_type_id == QuestionsTypes.Q38]
    thinking_types_result = []

    for answer in q38_answers:
        conclusion = "Не определено"
        if answer.conclusion_id == 1:
            conclusion = "Да"
        elif answer.conclusion_id == 2:
            conclusion = "Нет"
        elif answer.conclusion_id == 3:
            conclusion = "Условно присутствует"

        thinking_types_result.append({
            "thinking_type": answer.question.thinking_type.types_of_thinking_name,
            "conclusion": conclusion,
            "comments": answer.conclusion_text
        })

    values = {
        "thinking_types_results": json.dumps(thinking_types_result),
    }
    system = template.format(**values)
    print("System prompt: ========================================================================================")
    print(system)
    print("System prompt: ========================================================================================")

    print(f"Отправляем запрос к LLM {MODEL_NAME} для генерации заключения по опросу по Типам Мышления")
    answer_conclusion = llm_response_to_conclusion(system)
    print(f"Заключение по опросу по Типам Мышления:", answer_conclusion)
    
    return answer_conclusion

def ai_conclusion_questions15(survey: models.Survey, db: Session) -> str:
    """Заключение по третьему блоку из 15 вопросов (ценности)"""

    q15_answers = [answer for answer in survey.answers if answer.question.questions_type_id == QuestionsTypes.Q15]
    dialog = ""
    for answer in q15_answers:
        if answer.answer_text is None:
            continue
        dialog += f"Вопрос: {answer.question.question_text}\nОтвет: {answer.answer_text}\n"

    print("Диалог с испытуемым по выявлению ценностей:", dialog)
    system = f"""Ты — высокопрофессиональный психолог по диагностике ценностей испытуемого.
        На основе диалога с испытуемым проведи анализ ответов пользователя по следующим критериям и выдай результаты анализа:
        – то, как испытуемый хочет жить и к какому образу жизни стремитесь;
        – то, чем для испытуемый являются работа, деньги и проекты;
        – то, как испытуемый относится к людям, себе и своему достоинству;
        – то, как испытуемый понимает свободу и ответственность и какие действия считаете по-настоящему важными.
        Диалог с испытуемым по выявлению ценностей:
        {dialog}
    """

    print("Отправляем запрос к LLM для генерации заключения по первому блоку из 5 вопросов...")
    conclusion = llm_response_to_conclusion(system)
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
    print(f"Подключение к LLM {MODEL_NAME} выполнено. Получаем ответ от LLM...")
    response_content = chat_completion.choices[0].message.content.strip()
    print(f">>>>>>> Базовый вопрос: {question}")
    print(f"<<<<<<< Переформулированный вопрос: {response_content}")
    return response_content

def ai_transform_question_fallback(survey: models.Survey, question:models.Question, db: Session) -> str:
    """
    Трансформирует вопрос для лучшего понимания пользователем.
    Возвращает переформулированный текст вопроса.
    """
    history =""
    for answer in survey.answers:
        if answer.answer_text is None:
            continue
        question = db.query(models.Question).get(answer.question_id)
        if answer.reformulated_text is not None:
            history += f"Вопрос: {answer.reformulated_text}\nОтвет: {answer.answer_text}\n"
        else:
            history += f"Вопрос: {question.question_text}\nОтвет: {answer.answer_text}\n"

    client = OpenAI(
        api_key=PROXY_API_API_KEY,
        base_url=PROXY_API_OPENAI_BASE_URL,
    )
    
    system = f"""
        Ты — психолог по диагностике мышления. Проводишь 2 этап диагностики, направленный на выявление типов мышления.
        1. ТВОЯ ЗАДАЧА:
            Персонализировать БАЗОВЫЙ ВОПРОС согласно  ПРАВИЛАМ ТРАНСФОРМАЦИЯ ВОПРОСА. 
        2. РЕЗУЛЬТАТЫ ПЕРВИЧНОГО ОПРОСА:
            - ХОЧУ: {survey.desired_salary_level};
            - МОГУ: {survey.able_salary_level};
            - ДОСТОИН: {survey.decent_salary_level};
            - МЕЧТА: {survey.dreams};
            - СРОК ДОСТИЖЕНИЯ МЕЧТЫ: {survey.dreams_point};
            - ЗАКЛЮЧЕНИЕ: {survey.survey_conclusion_q05};
        3. ПРАВИЛА ТРАНСФОРМАЦИЯ ВОПРОСА из базового в персонализированный:
            3.1. УЧИТЫВАЕШЬ:
                    - МЕЧТУ клиента из первичного опроса;
                    - СРОК ДОСТИЖЕНИЯ МЕЧТЫ из первичного опроса;
                    - Разрыв между значениями ХОЧУ, МОГУ, ДОСТОИН из первичного опроса;
                    - ПРЕДЫДУЩИЕ ОТВЕТЫ КЛИЕНТА НА ВОПРОСЫ. Учитываешь стилистику и лексику ответов клиента на вопросы;
                - ХАРАКТЕРИСТИКИ БАЗОВОГО ВОПРОСА.
                3.2. Длина трансформированного вопроса должна быть не более 25 слов;
                3.3. Пиши понятные простые вопросы;
            3.4. ПРИМЕР:
                    Базовый вопрос: "Легко ли доводите дела до конца?"
                    С учётом того, что клиент мечтает о бизнесе, но ХОЧУ > МОГУ, где ХОЧУ=500000 и МОГУ=150000
                    Трансформированный вопрос следующий: "Вы мечтаете открыть свой бизнес, но пока зарабатываете меньше желаемого.
                    Когда возникает сложная задача — легко ли доводите её до конца?"
        4. ПРЕДЫДУЩИЕ ОТВЕТЫ КЛИЕНТА НА ВОПРОСЫ:
        {history}
        5. БАЗОВЫЙ ВОПРОС:
            - БАЗОВЫЙ ВОПРОС: {question.question_text};
            - ХАРАКТЕРИСТИКИ БАЗОВОГО ВОПРОСА:
                - фокус вопроса: {question.focus};
                - уточнение вопроса 1: {question.clarification_1};
                - уточнение вопроса 2: {question.clarification_2};
                - ключевые индикаторы: {question.key_indicators};
                - доказательства: {question.proof};
                - шаблон интерпредации: {question.interpretation_template}.
        """

    user = f"Переформулируй этот вопрос: {question}"

    messages = [
        {"role": "system", "content": system},
    ]

    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages
    )
    print(f"Подключение к LLM {MODEL_NAME} выполнено. Получаем ответ от LLM...")
    response_content = chat_completion.choices[0].message.content.strip()
    print(f">>>>>>> Базовый вопрос: {question.question_text}")
    print(f"<<<<<<< Трансформированный вопрос: {response_content}")
    return response_content

def ai_transform_question(survey: models.Survey, question:models.Question, db: Session) -> str:
    """
    Трансформирует вопрос для лучшего понимания пользователем.
    Возвращает переформулированный текст вопроса.
    """
    prompt_record = get_latest_prompt_by_type(db, PromptTypeEnum.QTRA)
    if not prompt_record:
        raise HTTPException(status_code=404, detail=f"Prompt for {PromptTypeEnum.QTRA} not found")
    
    template = prompt_record.prompt_text

    history =""
    for answer in survey.answers:
        if answer.answer_text is None:
            continue
        question = db.query(models.Question).get(answer.question_id)
        if answer.reformulated_text is not None:
            history += f"Вопрос: {answer.reformulated_text}\nОтвет: {answer.answer_text}\n"
        else:
            history += f"Вопрос: {question.question_text}\nОтвет: {answer.answer_text}\n"

    values = {
        # Параметры базового опроса из 5 вопросов
        "survey_desired_salary_level": survey.desired_salary_level,
        "survey_able_salary_level": survey.able_salary_level,
        "survey_decent_salary_level": survey.decent_salary_level,
        "survey_dreams": survey.dreams,
        "survey_dreams_point": survey.dreams_point,
        "survey_survey_conclusion_q05": survey.survey_conclusion_q05,
        # История ответов на предыдущие вопросы 
        "history": history,
        # Параметры вопроса
        "question_question_text": question.question_text,
        "question_focus": question.focus,
        "question_key_indicators": question.key_indicators,
        "question_proof": question.proof,
        "question_interpretation_template": question.interpretation_template,
    }
    print(f"Параметры для трансформации вопроса: {values}")
    client = OpenAI(
        api_key=PROXY_API_API_KEY,
        base_url=PROXY_API_OPENAI_BASE_URL,
    )
    system = template.format(**values)
    user = f"Переформулируй этот вопрос: {question}"
    messages = [
        {"role": "system", "content": system},
    ]
    print(f"Отправляем запрос к LLM для трансформации вопроса...")
    chat_completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages
    )
    print(f"Подключение к LLM {MODEL_NAME} выполнено. Получаем ответ от LLM...")
    response_content = chat_completion.choices[0].message.content.strip()
    print(f">>>>>>> Базовый вопрос: {question.question_text}")
    print(f"<<<<<<< Трансформированный вопрос: {response_content}")
    return response_content
