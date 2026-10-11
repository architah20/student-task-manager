import os

from flask import Flask

from .metrics import register_metrics
from .models import db
from .routes import bp


def create_app(test_config=None):
    """Application factory. Uses SQLite locally and PostgreSQL when DATABASE_URL is set."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///tasks.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    register_metrics(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app
