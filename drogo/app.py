from flask import Flask
from drogo.models import db
from drogo.views import views


def create_app(config={}):
    app = Flask(__name__, instance_relative_config=True)
    if not config:
        app.config.from_pyfile('settings.py')
    else:
        app.config.update(config)
    db.init_app(app)

    app.register_blueprint(views)
    return app
