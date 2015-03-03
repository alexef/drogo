from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.principal import Principal
from drogo.models import db, User
from drogo.views import views


def create_app(config={}):
    app = Flask(__name__, instance_relative_config=True)
    if not config:
        app.config.from_pyfile('settings.py')
    else:
        app.config.update(config)
    db.init_app(app)
    app.register_blueprint(views)

    app.secret_key = app.config['PRIVATE_KEY']

    if app.config.get('SENTRY_DSN'):
        from raven.contrib.flask import Sentry
        Sentry(app)

    login_manager = LoginManager()
    @login_manager.user_loader
    def load_user(userid):
        try:
            return User.query.get(userid)
        except:
            return None
    login_manager.setup_app(app)

    Principal(app)

    return app
