import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Базовая конфигурация приложения."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"

    # Пути к данным (пока JSON-файлы вместо БД).
    # ВАЖНО: на Railway (и большинстве PaaS) файловая система контейнера не персистентна —
    # всё записанное на диск стирается при каждом передеплое. Чтобы XP пользователей и
    # регистрации не терялись, смонтируйте Railway Volume (Settings → Volumes) и укажите
    # его путь в переменной окружения DATA_DIR (например: /data). Места (places.json) можно
    # оставить в коде — они не изменяются в рантайме и передеплой им не страшен.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
    PLACES_FILE = os.path.join(BASE_DIR, "data", "places.json")  # статичные данные — всегда из кода
    TOURS_FILE = os.path.join(BASE_DIR, "data", "tours.json")
    HOTELS_FILE = os.path.join(BASE_DIR, "data", "hotels.json")
    CARS_FILE = os.path.join(BASE_DIR, "data", "cars.json")
    USERS_FILE = os.path.join(DATA_DIR, "users.json")
    BOOKING_REQUESTS_FILE = os.path.join(DATA_DIR, "booking_requests.json")
