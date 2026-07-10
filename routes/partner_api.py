"""
B2B API для партнёров. На этапе MVP — упрощённая заглушка без JWT и без реальной
изоляции данных по партнёрам. Перед реальным подключением партнёров нужно:
1. Добавить полноценную аутентификацию по JWT с ограниченным сроком действия.
2. Хранить данные каждого партнёра в изолированных таблицах/схемах БД.
3. Добавить валидацию присылаемых партнёром данных (например, через pydantic).
"""

from flask import Blueprint, request, jsonify

partner_bp = Blueprint("partner", __name__)

# Временное хранилище заявок партнёров (демо, не для продакшена)
_partner_submissions = []


@partner_bp.route("/api/partner/submit-place", methods=["POST"])
def submit_place():
    data = request.get_json(force=True, silent=True) or {}

    required_fields = ["name", "category", "region", "description"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Не заполнены поля: {', '.join(missing)}"}), 400

    _partner_submissions.append(data)
    return jsonify({"status": "ok", "message": "Заявка принята на модерацию"}), 201


@partner_bp.route("/api/partner/submissions")
def list_submissions():
    # В демо-версии доступно без авторизации — в проде закрыть JWT-токеном партнёра
    return jsonify(_partner_submissions)
