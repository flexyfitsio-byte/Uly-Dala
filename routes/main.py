import copy
from flask import Blueprint, render_template, jsonify, request
from database.db_manager import get_all_places, get_place_by_id

main_bp = Blueprint("main", __name__)


def _strip_quiz_answer(place):
    """Никогда не отдаём клиенту правильный индекс ответа — иначе викторину легко обмануть
    через вкладку Network. Сервер проверяет ответ отдельно, в /api/quiz/<id>."""
    safe = copy.deepcopy(place)
    if "quiz" in safe and "correct" in safe["quiz"]:
        del safe["quiz"]["correct"]
    return safe


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/chat")
def chat_page():
    return render_template("chat.html")


@main_bp.route("/partner")
def partner_page():
    return render_template("partner.html")


@main_bp.route("/api/places")
def api_places():
    category = request.args.get("category")
    region = request.args.get("region")
    places = get_all_places()

    if category:
        places = [p for p in places if p["category"] == category]
    if region:
        places = [p for p in places if p["region"] == region]

    return jsonify([_strip_quiz_answer(p) for p in places])


@main_bp.route("/api/places/<int:place_id>")
def api_place_detail(place_id):
    place = get_place_by_id(place_id)
    if not place:
        return jsonify({"error": "Место не найдено"}), 404
    return jsonify(_strip_quiz_answer(place))
