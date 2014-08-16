from flask import Flask
from drogo.models import db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('settings.py')
    db.init_app(app)

    return app
