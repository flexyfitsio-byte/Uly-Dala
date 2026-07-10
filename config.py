import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Базовая конфигурация приложения."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"

    # Пути к данным (пока JSON-файлы вместо БД)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PLACES_FILE = os.path.join(DATA_DIR, "places.json")
    USERS_FILE = os.path.join(DATA_DIR, "users.json")
