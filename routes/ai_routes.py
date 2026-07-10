from flask import Blueprint, request, jsonify
from ai_engine.openai_client import generate_intelligent_route, ask_historian
from database.db_manager import get_place_by_id

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/api/ai/route", methods=["POST"])
def api_generate_route():
    data = request.get_json(force=True, silent=True) or {}

    user_request = data.get("message", "").strip()
    budget = data.get("budget")
    days = data.get("days", 2)
    category = data.get("category")

    if not user_request:
        return jsonify({"error": "Опишите, куда хотите поехать"}), 400

    try:
        budget = int(budget) if budget else None
        days = int(days)
    except (TypeError, ValueError):
        return jsonify({"error": "Бюджет и количество дней должны быть числами"}), 400

    result = generate_intelligent_route(user_request, user_budget=budget, user_days=days, category=category)
    return jsonify(result)


@ai_bp.route("/api/ai/historian/<int:place_id>", methods=["POST"])
def api_ask_historian(place_id):
    data = request.get_json(force=True, silent=True) or {}
    question = data.get("question", "").strip()
    mode = data.get("mode", "для туриста")

    place = get_place_by_id(place_id)
    if not place:
        return jsonify({"error": "Место не найдено"}), 404

    if not question:
        question = "Расскажи об этом месте"

    result = ask_historian(place, question, mode=mode)
    return jsonify(result)
