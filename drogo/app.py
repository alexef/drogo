from flask import Flask
from flask.ext.login import LoginManager
from drogo.models import db
from drogo.views import views
from drogo.auth import LdapUser


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
        return LdapUser(uid=userid)
    login_manager.setup_app(app)

    return app
