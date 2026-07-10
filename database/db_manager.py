"""
Слой доступа к данным. На старте MVP используем JSON-файлы вместо БД.
Интерфейс функций сделан так, чтобы позже безболезненно перейти на PostgreSQL:
достаточно будет переписать реализацию внутри функций, не трогая роуты.
"""

import json
import os
import threading
from config import Config

_lock = threading.Lock()


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, data):
    with _lock:
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


def get_verified_places(max_budget=None, category=None, region=None):
    """Возвращает места, отфильтрованные по бюджету/категории/региону.
    Используется ИИ-гидом — модель не может "придумывать" места вне этого списка."""
    places = get_all_places()

    if max_budget is not None:
        places = [p for p in places if p["avg_cost_per_day"] <= max_budget]
    if category:
        places = [p for p in places if p["category"] == category]
    if region:
        places = [p for p in places if p["region"] == region]

    return places


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
    if place_id not in user["visited_places"]:
        user["visited_places"].append(place_id)
        place = get_place_by_id(place_id)
        if place:
            region = place["region"]
            user["regions_progress"][region] = user["regions_progress"].get(region, 0) + 1
    users[user_id] = user
    _write_json(Config.USERS_FILE, users)
    return user


def answer_quiz(user_id, place_id, selected_index):
    place = get_place_by_id(place_id)
    if not place or "quiz" not in place:
        return {"correct": False, "xp_gained": 0}

    is_correct = selected_index == place["quiz"]["correct"]
    xp_gained = 50 if is_correct else 0

    users = _get_users()
    user = users.get(user_id, dict(DEFAULT_USER))
    key = f"{place_id}"
    if key not in user["quiz_answered"]:
        user["quiz_answered"].append(key)
        if xp_gained:
            user["xp"] += xp_gained
            user["level"] = _calc_level(user["xp"])
    users[user_id] = user
    _write_json(Config.USERS_FILE, users)

    return {"correct": is_correct, "xp_gained": xp_gained}
