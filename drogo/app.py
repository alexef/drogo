from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.principal import Principal, RoleNeed, identity_loaded
from flask.ext.admin import Admin
from drogo.models import db, User
from drogo.views import views, AdminUserView


def create_app(config={}):
    app = Flask(__name__, instance_relative_config=True)
    if not config:
        app.config.from_pyfile('settings.py')
    else:
        app.config.update(config)
    db.init_app(app)
    app.register_blueprint(views)

    app.secret_key = app.config['PRIVATE_KEY']
    app.config['DEBUG'] = True

    if app.config.get('SENTRY_DSN'):
        from raven.contrib.flask import Sentry
        Sentry(app)

    @app.errorhandler(403)
    def permission_denied(error):
        return "Permission denied", 403

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        if identity.id:
            user = User.query.get(identity.id)
            if user and user.is_admin:
                identity.provides.add(RoleNeed('admin'))

    login_manager = LoginManager()
    @login_manager.user_loader
    def load_user(userid):
        try:
            return User.query.get(userid)
        except:
            return None
    login_manager.setup_app(app)

    Principal(app)
    admin = Admin(app)
    admin.add_view(AdminUserView(db.session))

    return app
