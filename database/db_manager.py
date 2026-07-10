"""
Слой доступа к данным. На старте MVP используем JSON-файлы вместо БД.
Интерфейс функций сделан так, чтобы позже безболезненно перейти на PostgreSQL:
достаточно будет переписать реализацию внутри функций, не трогая роуты.
"""

import json
import os
import threading
from datetime import datetime, timezone
from config import Config

_lock = threading.Lock()


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, data):
    with _lock:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- Места ----------

def get_all_places():
    return _read_json(Config.PLACES_FILE, [])


def get_place_by_id(place_id):
    places = get_all_places()
    for p in places:
        if p["id"] == int(place_id):
            return p
    return None


def _place_categories(place):
    """Место может относиться к нескольким категориям (например nature + adventure)."""
    return place.get("categories") or [place.get("category")]


def get_verified_places(max_budget=None, category=None, region=None):
    """Возвращает места, отфильтрованные по бюджету/категории/региону.
    Используется ИИ-гидом — модель не может "придумывать" места вне этого списка."""
    places = get_all_places()

    if max_budget is not None:
        places = [p for p in places if p["avg_cost_per_day"] <= max_budget]
    if category:
        places = [p for p in places if category in _place_categories(p)]
    if region:
        places = [p for p in places if p["region"] == region]

    return places


# ---------- Туры / Отели / Авто (каталоги-витрины) ----------
# Пока без реальной интеграции с бронированием — см. save_booking_request().

def get_all_tours():
    return _read_json(Config.TOURS_FILE, [])


def get_all_hotels():
    return _read_json(Config.HOTELS_FILE, [])


def get_all_cars():
    return _read_json(Config.CARS_FILE, [])


def save_booking_request(payload):
    """
    Сохраняет заявку на бронирование (тур/отель/авто/билеты) — ДЕМО-РЕЖИМ.
    Реального бронирования и оплаты нет: это лид для менеджера, как форма
    "перезвоните мне". Полноценное бронирование потребует партнёрского API
    (Aviasales/Kiwi, Booking.com Affiliate, локальные агрегаторы вроде
    Chocotravel/Aviata) — их нужно подключать отдельно, когда появятся ключи.
    """
    requests_list = _read_json(Config.BOOKING_REQUESTS_FILE, [])
    payload["id"] = len(requests_list) + 1
    requests_list.append(payload)
    _write_json(Config.BOOKING_REQUESTS_FILE, requests_list)
    return payload


# ---------- Пользователи (геймификация) ----------

DEFAULT_USER = {
    "xp": 0,
    "level": "Новичок",
    "visited_places": [],
    "quiz_answered": [],
    "regions_progress": {}
}

LEVELS = [
    (0, "Новичок"),
    (300, "Путешественник"),
    (800, "Исследователь"),
    (1800, "Знаток Казахстана"),
    (3500, "Легенда Великой степи"),
]


def _get_users():
    return _read_json(Config.USERS_FILE, {})


def get_user(user_id):
    users = _get_users()
    if user_id not in users:
        users[user_id] = dict(DEFAULT_USER)
        _write_json(Config.USERS_FILE, users)
    return users[user_id]


def _calc_level(xp):
    level_name = LEVELS[0][1]
    for threshold, name in LEVELS:
        if xp >= threshold:
            level_name = name
    return level_name


def add_xp(user_id, amount, reason=""):
    users = _get_users()
    user = users.get(user_id, dict(DEFAULT_USER))
    user["xp"] = user.get("xp", 0) + amount
    user["level"] = _calc_level(user["xp"])
    users[user_id] = user
    _write_json(Config.USERS_FILE, users)
    return user


def mark_place_visited(user_id, place_id):
    users = _get_users()
    user = users.get(user_id, dict(DEFAULT_USER))
    user.setdefault("visited_places", [])

    visited_ids = [v["place_id"] if isinstance(v, dict) else v for v in user["visited_places"]]
    is_new_visit = place_id not in visited_ids

    if is_new_visit:
        user["visited_places"].append({
            "place_id": place_id,
            "visited_at": datetime.now(timezone.utc).isoformat(),
        })
        place = get_place_by_id(place_id)
        if place:
            region = place["region"]
            user["regions_progress"][region] = user["regions_progress"].get(region, 0) + 1

    users[user_id] = user
    _write_json(Config.USERS_FILE, users)
    return user, is_new_visit


def get_visit_history(user_id):
    """Список посещённых мест с датой и деталями места — для страницы профиля."""
    user = get_user(user_id)
    history = []
    for v in user.get("visited_places", []):
        place_id = v["place_id"] if isinstance(v, dict) else v
        visited_at = v.get("visited_at") if isinstance(v, dict) else None
        place = get_place_by_id(place_id)
        if place:
            history.append({
                "place_id": place_id,
                "name": place["name"],
                "region": place["region"],
                "visited_at": visited_at,
            })
    history.sort(key=lambda x: x["visited_at"] or "", reverse=True)
    return history


def answer_quiz(user_id, place_id, selected_index):
    place = get_place_by_id(place_id)
    if not place or "quiz" not in place:
        return {"correct": False, "xp_gained": 0, "already_answered": False}

    is_correct = selected_index == place["quiz"]["correct"]

    users = _get_users()
    user = users.get(user_id, dict(DEFAULT_USER))
    key = f"{place_id}"
    already_answered = key in user["quiz_answered"]
    xp_gained = 0

    if not already_answered:
        user["quiz_answered"].append(key)
        if is_correct:
            xp_gained = 50
            user["xp"] += xp_gained
            user["level"] = _calc_level(user["xp"])

    users[user_id] = user
    _write_json(Config.USERS_FILE, users)

    return {"correct": is_correct, "xp_gained": xp_gained, "already_answered": already_answered}


# ---------- Отзывы ----------

REVIEWS_FILE_NAME = "reviews.json"


def _reviews_path():
    return os.path.join(Config.DATA_DIR, REVIEWS_FILE_NAME)


def get_reviews_for_place(place_id):
    reviews = _read_json(_reviews_path(), [])
    place_reviews = [r for r in reviews if r["place_id"] == int(place_id)]
    place_reviews.sort(key=lambda r: r["created_at"], reverse=True)
    return place_reviews


def get_place_rating_summary(place_id):
    reviews = get_reviews_for_place(place_id)
    if not reviews:
        return {"average": None, "count": 0}
    avg = sum(r["rating"] for r in reviews) / len(reviews)
    return {"average": round(avg, 1), "count": len(reviews)}


def add_review(place_id, user_id, author_name, rating, text):
    reviews = _read_json(_reviews_path(), [])

    review = {
        "id": len(reviews) + 1,
        "place_id": int(place_id),
        "user_id": user_id,
        "author_name": author_name or "Гость",
        "rating": max(1, min(5, int(rating))),
        "text": (text or "").strip()[:800],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    reviews.append(review)
    _write_json(_reviews_path(), reviews)
    return review

