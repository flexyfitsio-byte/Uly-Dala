import json
from config import Config
from ai_engine.prompts import ROUTE_SYSTEM_PROMPT, HISTORIAN_SYSTEM_PROMPT, contains_suspicious_instruction
from ai_engine.rag_service import build_context

_client = None


def _get_client():
    """Ленивая инициализация клиента OpenAI (только если задан ключ)."""
    global _client
    if _client is None and Config.OPENAI_API_KEY:
        from openai import OpenAI
        _client = OpenAI(api_key=Config.OPENAI_API_KEY)
    return _client


def generate_intelligent_route(user_request: str, user_budget: int = None, user_days: int = 2, category: str = None):
    """
    Генерирует маршрут строго на основе реальных данных (RAG).
    Если OPENAI_API_KEY не задан — возвращает демо-заглушку на основе тех же данных,
    чтобы MVP можно было тестировать без ключа API.
    """
    if contains_suspicious_instruction(user_request):
        return {"error": "Запрос содержит недопустимые инструкции. Переформулируйте, пожалуйста."}

    places = build_context(max_budget=user_budget, category=category)

    if not places:
        return {"error": "Подходящих мест не найдено. Попробуйте изменить бюджет или категорию."}

    client = _get_client()

    if client is None:
        # ---- Демо-режим без ключа OpenAI: простая детерминированная сборка маршрута ----
        return _mock_route(places, user_days, user_budget)

    system_instruction = ROUTE_SYSTEM_PROMPT.format(places_json=json.dumps(places, ensure_ascii=False))

    response_schema_hint = (
        "Ответ строго в формате JSON со следующей структурой: "
        '{"destination_name": str, "total_estimated_cost": int, '
        '"days": [{"day_number": int, "activities": [{"time": str, "location": str, '
        '"description": str, "cost": int}]}]}'
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction + "\n\n" + response_schema_hint},
                {"role": "user", "content": f"Запрос: '{user_request}'. Бюджет: {user_budget}. Дней: {user_days}."},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw_output = response.choices[0].message.content
        return json.loads(raw_output)
    except Exception as e:
        return {"error": f"Ошибка генерации маршрута: {e}"}


def _mock_route(places, user_days, user_budget):
    """Простейшая заглушка маршрута для демо без API-ключа."""
    chosen = places[: max(1, min(len(places), user_days + 1))]
    days = []
    total_cost = 0
    for i in range(user_days):
        place = chosen[i % len(chosen)]
        cost = place["avg_cost_per_day"]
        total_cost += cost
        days.append({
            "day_number": i + 1,
            "activities": [
                {"time": "09:00", "location": place["name"], "description": place["description"], "cost": cost}
            ],
        })

    return {
        "destination_name": chosen[0]["name"],
        "total_estimated_cost": total_cost,
        "days": days,
        "note": "Демо-режим (без OPENAI_API_KEY): маршрут собран по простым правилам, не через LLM.",
    }


def ask_historian(place: dict, question: str, mode: str = "для туриста"):
    """ИИ-историк: отвечает на вопрос о месте, используя только предоставленные факты."""
    if contains_suspicious_instruction(question):
        return {"error": "Запрос содержит недопустимые инструкции."}

    client = _get_client()

    if client is None:
        return {"answer": place.get("history", "История этого места пока не добавлена."), "note": "Демо-режим без OPENAI_API_KEY."}

    system_instruction = HISTORIAN_SYSTEM_PROMPT.format(
        place_json=json.dumps(place, ensure_ascii=False), mode=mode
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"error": f"Ошибка ИИ-историка: {e}"}
