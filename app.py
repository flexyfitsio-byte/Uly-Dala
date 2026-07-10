from flask import Flask
from config import Config

from routes.main import main_bp
from routes.auth import auth_bp
from routes.ai_routes import ai_bp
from routes.gamification import gamification_bp
from routes.partner_api import partner_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(gamification_bp)
    app.register_blueprint(partner_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
