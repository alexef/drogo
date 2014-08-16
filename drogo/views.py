from flask import Blueprint, redirect, url_for, render_template, request
from flask.views import MethodView
from drogo.models import Project, User, Worktime

views = Blueprint('views', __name__)


class Homepage(MethodView):
    def get(self):
        return render_template('homepage.html')


class ProjectView(MethodView):
    def get(self, project_id=None):
        project = project_id and Project.query.get(project_id)
        projects = Project.query.order_by(Project.slug)
        return render_template('project.html', project=project,
                               projects=projects)


class UserView(MethodView):
    def get(self, user_id=None):
        user = user_id and User.query.get(user_id)
        users = User.query.all()
        month = request.args.get('month')
        if month:
            worktimes = user.month_worktimes(month)
        else:
            worktimes = user.last_worktimes
        total = sum([wt.hours or 0 for wt in worktimes])
        return render_template('user.html', users=users, user=user,
                               month=month, worktimes=worktimes, total=total)


# utils
@views.add_app_template_global
def active(text):
    if text in request.url:
        return 'class=active'
    return ''


# urls.py
views.add_url_rule('/', view_func=Homepage.as_view('homepage'))
views.add_url_rule('/project/<project_id>',
                   view_func=ProjectView.as_view('project'))
views.add_url_rule('/project/all', view_func=ProjectView.as_view('projects'))
views.add_url_rule('/user/<user_id>', view_func=UserView.as_view('user'))
views.add_url_rule('/user/all', view_func=UserView.as_view('users'))
