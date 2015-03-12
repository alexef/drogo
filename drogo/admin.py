from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import current_user


class AdminRequiredMixin(object):
    def is_accessible(self):
        return current_user.is_authenticated() and current_user.is_admin


class AdminModelView(ModelView, AdminRequiredMixin):
    pass


