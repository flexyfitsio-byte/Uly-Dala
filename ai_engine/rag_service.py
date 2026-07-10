"""
RAG (Retrieval-Augmented Generation) слой.
Забирает из данных только релевантные места, чтобы ИИ не "галлюцинировал"
несуществующие локации, цены или маршруты.
"""

from database.db_manager import get_verified_places


def build_context(max_budget=None, category=None, region=None):
    """Возвращает список проверенных мест, подходящих под параметры запроса."""
    places = get_verified_places(max_budget=max_budget, category=category, region=region)

    # Оставляем только нужные ИИ поля, чтобы не раздувать промт
    trimmed = [
        {
            "id": p["id"],
            "name": p["name"],
            "region": p["region"],
            "category": p["category"],
            "description": p["description"],
            "avg_cost_per_day": p["avg_cost_per_day"],
            "tags": p["tags"],
        }
        for p in places
    ]
    return trimmed
