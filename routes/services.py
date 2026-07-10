"""
Роуты для витрин "Туры", "Отели", "Аренда авто" и "Авиа/ЖД билеты".

ВАЖНО: это MVP-заглушки. Каталоги (туры/отели/авто) — демо-данные, а не живая
инвентаризация от поставщиков. Кнопка "Забронировать" не проводит оплату —
она сохраняет заявку (лид), как форма "перезвоните мне". Настоящее бронирование
с реальными ценами и наличием требует партнёрского API:
- Авиа/ЖД: Aviasales/Kiwi, Chocotravel, Aviata
- Отели: Booking.com Affiliate, Ostrovok
- Авто: локальные прокат-компании или агрегатор вроде Sixt/Localrent

Как только появятся API-ключи от партнёров — эти роуты нужно будет заменить
на реальные вызовы вместо data/*.json.
"""

from flask import Blueprint, render_template, request, jsonify
from database.db_manager import get_all_tours, get_all_hotels, get_all_cars, save_booking_request

services_bp = Blueprint("services", __name__)


@services_bp.route("/tours")
def tours_page():
    return render_template("tours.html")


@services_bp.route("/hotels")
def hotels_page():
    return render_template("hotels.html")


@services_bp.route("/cars")
def cars_page():
    return render_template("cars.html")


@services_bp.route("/flights")
def flights_page():
    return render_template("flights.html")


@services_bp.route("/api/tours")
def api_tours():
    return jsonify(get_all_tours())


@services_bp.route("/api/hotels")
def api_hotels():
    return jsonify(get_all_hotels())


@services_bp.route("/api/cars")
def api_cars():
    return jsonify(get_all_cars())


@services_bp.route("/api/booking-request", methods=["POST"])
def api_booking_request():
    data = request.get_json(force=True, silent=True) or {}

    required = ["service_type", "item_name", "contact_name", "contact_phone"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Не заполнены поля: {', '.join(missing)}"}), 400

    saved = save_booking_request(data)
    return jsonify({
        "status": "ok",
        "message": "Заявка принята! Менеджер свяжется с вами в течение 24 часов для подтверждения.",
        "request_id": saved["id"],
    }), 201
