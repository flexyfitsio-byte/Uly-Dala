from flask import Blueprint, request, jsonify, session
from database.db_manager import get_place_by_id, get_reviews_for_place, get_place_rating_summary, add_review

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("/api/places/<int:place_id>/reviews", methods=["GET"])
def api_get_reviews(place_id):
    if not get_place_by_id(place_id):
        return jsonify({"error": "Место не найдено"}), 404

    return jsonify({
        "reviews": get_reviews_for_place(place_id),
        "summary": get_place_rating_summary(place_id),
    })


@reviews_bp.route("/api/places/<int:place_id>/reviews", methods=["POST"])
def api_add_review(place_id):
    place = get_place_by_id(place_id)
    if not place:
        return jsonify({"error": "Место не найдено"}), 404

    data = request.get_json(force=True, silent=True) or {}
    rating = data.get("rating")
    text = (data.get("text") or "").strip()
    author_name = (data.get("author_name") or session.get("name") or session.get("email") or "Гость").strip()

    if not rating:
        return jsonify({"error": "Укажите оценку от 1 до 5"}), 400
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "Оценка должна быть числом от 1 до 5"}), 400
    if not (1 <= rating <= 5):
        return jsonify({"error": "Оценка должна быть от 1 до 5"}), 400
    if not text:
        return jsonify({"error": "Напишите короткий отзыв"}), 400

    user_id = session.get("user_id", "guest")
    review = add_review(place_id, user_id, author_name, rating, text)
    return jsonify({"review": review, "summary": get_place_rating_summary(place_id)}), 201
