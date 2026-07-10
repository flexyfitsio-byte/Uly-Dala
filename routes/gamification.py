import uuid
from flask import Blueprint, request, jsonify, session
from database.db_manager import get_user, add_xp, mark_place_visited, answer_quiz

gamification_bp = Blueprint("gamification", __name__)


def _current_user_id():
    """Для гостей без регистрации используем анонимный ID в сессии."""
    if "user_id" not in session:
        session["user_id"] = f"guest-{uuid.uuid4()}"
    return session["user_id"]


@gamification_bp.route("/api/profile")
def api_profile():
    user_id = _current_user_id()
    return jsonify(get_user(user_id))


@gamification_bp.route("/api/visit/<int:place_id>", methods=["POST"])
def api_visit(place_id):
    user_id = _current_user_id()
    user = mark_place_visited(user_id, place_id)
    user = add_xp(user_id, 100, reason="visit")
    return jsonify(user)


@gamification_bp.route("/api/quiz/<int:place_id>", methods=["POST"])
def api_quiz(place_id):
    data = request.get_json(force=True, silent=True) or {}
    selected_index = data.get("selected_index")

    if selected_index is None:
        return jsonify({"error": "Не выбран вариант ответа"}), 400

    user_id = _current_user_id()
    result = answer_quiz(user_id, place_id, int(selected_index))
    return jsonify(result)
