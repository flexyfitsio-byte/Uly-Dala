import json
import re
from config import Config
from ai_engine.prompts import ROUTE_SYSTEM_PROMPT, HISTORIAN_SYSTEM_PROMPT, contains_suspicious_instruction
from ai_engine.rag_service import build_context

_client = None
_active_model = None


def _get_client():
    """Ленивая инициализация клиента ИИ-провайдера, выбранного в Config.AI_PROVIDER.
    Groq (Llama 3), xAI (Grok) и OpenAI используют один и тот же OpenAI SDK —
    отличаются только api_key, base_url и имя модели."""
    global _client, _active_model

    provider_cfg = Config.AI_PROVIDERS.get(Config.AI_PROVIDER, {})
    api_key = provider_cfg.get("api_key")

    if not api_key:
        return None

    if _client is None:
        from openai import OpenAI
        kwargs = {"api_key": api_key}
        if provider_cfg.get("base_url"):
            kwargs["base_url"] = provider_cfg["base_url"]
        _client = OpenAI(**kwargs)
        _active_model = provider_cfg.get("model")

    return _client


def _extract_json(raw_text):
    """Некоторые провайдеры (особенно без строгого JSON-режима) иногда оборачивают
    JSON в markdown-код или добавляют пояснение до/после. Достаём JSON-объект надёжно."""
    raw_text = raw_text.strip()
    raw_text = re.sub(r"^```(json)?|```$", "", raw_text, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


RESPONSE_SCHEMA_HINT = (
    "Ответ строго в формате JSON (без markdown, без пояснений вне JSON) со структурой: "
    '{"destination_name": str, "total_estimated_cost": int, '
    '"days": [{"day_number": int, "activities": [{"time": str, "location": str, '
    '"description": str, "cost": int}]}], "reply": str}. '
    'Поле "reply" — короткий (1-2 предложения) человеческий ответ пользователю о том, '
    'что изменилось в маршруте или почему собран именно такой вариант.'
)


def generate_intelligent_route(user_request, user_budget=None, user_days=2, category=None,
                                history=None, last_route=None):
    """
    Генерирует или ДОРАБАТЫВАЕТ маршрут строго на основе реальных данных (RAG).

    history — список предыдущих сообщений диалога [{"role": "user"/"assistant", "content": str}],
    last_route — последний собранный маршрут (dict), если пользователь просит его изменить
    ("сделай дешевле", "добавь красивые места" и т.п.).

    Если для выбранного AI_PROVIDER не задан ключ — работает в демо-режиме: простые правила вместо LLM,
    но с той же логикой "уточнения" предыдущего маршрута.
    """
    if contains_suspicious_instruction(user_request):
        return {"error": "Запрос содержит недопустимые инструкции. Переформулируйте, пожалуйста."}

    places = build_context(max_budget=user_budget, category=category)

    if not places:
        return {"error": "Подходящих мест не найдено. Попробуйте изменить бюджет или категорию."}

    client = _get_client()

    if client is None:
        # ---- Демо-режим без ключа OpenAI: правила вместо LLM, но с поддержкой уточнений ----
        return _mock_route(places, user_days, user_budget, user_request, last_route)

    system_instruction = ROUTE_SYSTEM_PROMPT.format(places_json=json.dumps(places, ensure_ascii=False))

    messages = [{"role": "system", "content": system_instruction + "\n\n" + RESPONSE_SCHEMA_HINT}]

    # Полная история диалога — благодаря ей ИИ помнит, что просили раньше ("сделай дешевле" и т.п.)
    for turn in (history or []):
        messages.append({"role": turn["role"], "content": turn["content"]})

    context_note = f"Бюджет: {user_budget}. Дней: {user_days}."
    if last_route:
        context_note += f" Текущий маршрут (доработай его, если просьба это подразумевает): {json.dumps(last_route, ensure_ascii=False)}"

    messages.append({"role": "user", "content": f"{user_request}\n\n[{context_note}]"})

    try:
        try:
            response = client.chat.completions.create(
                model=_active_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except Exception:
            # Не все провайдеры/модели поддерживают response_format=json_object —
            # повторяем без него и вытаскиваем JSON из текста вручную.
            response = client.chat.completions.create(
                model=_active_model,
                messages=messages,
                temperature=0.3,
            )
        raw_output = response.choices[0].message.content
        return _extract_json(raw_output)
    except Exception as e:
        return {"error": f"Ошибка генерации маршрута ({Config.AI_PROVIDER}): {e}"}


def _mock_route(places, user_days, user_budget, user_request, last_route):
    """
    Демо-режим без LLM. Умеет не только собрать маршрут с нуля, но и ОТРЕАГИРОВАТЬ
    на типовые уточнения, если есть предыдущий маршрут — чтобы диалог не выглядел
    как набор несвязанных ответов.
    """
    text = user_request.lower()
    by_id = {p["id"]: p for p in places}

    def render(chosen_places, note, reply):
        days = []
        total_cost = 0
        for i in range(len(chosen_places)):
            place = chosen_places[i]
            cost = place["avg_cost_per_day"]
            total_cost += cost
            days.append({
                "day_number": i + 1,
                "activities": [
                    {"time": "09:00", "location": place["name"], "description": place["description"], "cost": cost}
                ],
            })
        return {
            "destination_name": chosen_places[0]["name"] if chosen_places else "—",
            "total_estimated_cost": total_cost,
            "days": days,
            "note": note,
            "reply": reply,
        }

    demo_note = f"Демо-режим (нет ключа для {Config.AI_PROVIDER}): маршрут собран по простым правилам, не через LLM."

    # --- Уточнение существующего маршрута ---
    if last_route and last_route.get("days"):
        current_ids = []
        for day in last_route["days"]:
            for act in day["activities"]:
                match = next((p for p in places if p["name"] == act["location"]), None)
                if match:
                    current_ids.append(match["id"])

        if any(w in text for w in ["дешевле", "дешевый", "бюджетн"]):
            cheaper = sorted(places, key=lambda p: p["avg_cost_per_day"])[: max(1, len(current_ids) or 2)]
            return render(cheaper, demo_note, "Собрал вариант подешевле из доступных мест.")

        if any(w in text for w in ["дорож", "премиум", "получше", "покомфортн"]):
            pricier = sorted(places, key=lambda p: -p["avg_cost_per_day"])[: max(1, len(current_ids) or 2)]
            return render(pricier, demo_note, "Заменил на более дорогие и статусные места.")

        if any(w in text for w in ["добавь", "больше мест", "ещё одно", "еще одно"]):
            remaining = [p for p in places if p["id"] not in current_ids]
            extended = [by_id[i] for i in current_ids if i in by_id] + remaining[:1]
            return render(extended or places[:2], demo_note, "Добавил ещё одно место в маршрут.")

        if any(w in text for w in ["красив", "живописн", "природ"]):
            nature = [p for p in places if p["category"] == "nature"]
            return render(nature or places[:2], demo_note, "Сделал упор на самые живописные природные локации.")

        if any(w in text for w in ["короче", "меньше дней", "убери"]):
            shorter = [by_id[i] for i in current_ids if i in by_id][:-1] or places[:1]
            return render(shorter, demo_note, "Сократил маршрут на один день.")

    # --- Свежая генерация с нуля ---
    chosen = places[: max(1, min(len(places), user_days + 1))]
    chosen_for_days = [chosen[i % len(chosen)] for i in range(user_days)]
    return render(chosen_for_days, demo_note, f"Собрал маршрут на {user_days} дн. под бюджет {user_budget or 'без ограничений'} ₸/день.")


def ask_historian(place: dict, question: str, mode: str = "для туриста"):
    """ИИ-историк: отвечает на вопрос о месте, используя только предоставленные факты."""
    if contains_suspicious_instruction(question):
        return {"error": "Запрос содержит недопустимые инструкции."}

    client = _get_client()

    if client is None:
        return {"answer": place.get("history", "История этого места пока не добавлена."), "note": f"Демо-режим (нет ключа для {Config.AI_PROVIDER})."}

    system_instruction = HISTORIAN_SYSTEM_PROMPT.format(
        place_json=json.dumps(place, ensure_ascii=False), mode=mode
    )

    try:
        response = client.chat.completions.create(
            model=_active_model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"error": f"Ошибка ИИ-историка ({Config.AI_PROVIDER}): {e}"}
