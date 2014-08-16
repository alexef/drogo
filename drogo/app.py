from flask import Flask
from drogo.models import db
from drogo.views import views


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('settings.py')
    db.init_app(app)

    app.register_blueprint(views)
    return app
