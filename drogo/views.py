from collections import OrderedDict
from datetime import date
from flask import Blueprint, redirect, url_for, render_template, request
from flask.views import MethodView
from sqlalchemy import func
from drogo.models import Project, User, Worktime

views = Blueprint('views', __name__)


class Homepage(MethodView):
    def get(self):
        return render_template('homepage.html', users=User.query.count(),
                               projects=Project.query.count())


class ProjectView(MethodView):
    def get(self, project_id=None):
        project = project_id and Project.query.get(project_id)
        projects = Project.query.order_by(Project.slug)
        return render_template('project.html', project=project,
                               projects=projects)


class ProjectMonthlyView(MethodView):
    def get(self, project_id):
        project = Project.query.get_or_404(project_id)
        projects = Project.query.order_by(Project.slug)
        month = request.args.get('month')
        worktimes = project.month_worktimes(month)
        return render_template('project_month.html', project=project,
                               projects=projects, month=month,
                               worktimes=worktimes)


class UserAll(MethodView):
    def get(self):
        return render_template('user/user.html', user=None,
                               users=User.query.all())


class UserMixin(object):
    def get_context(self, user_id):
        self.month = request.args.get('month', date.today().strftime("%Y-%m"))
        self.user = User.query.get_or_404(user_id)
        self.worktimes = self.user.month_worktimes(self.month)

        total = sum([wt.hours or 0 for wt in self.worktimes])
        return {
            'users': User.query.all(),
            'month': self.month,
            'user': self.user,
            'worktimes': self.worktimes,
            'total': total,
        }


class UserView(UserMixin, MethodView):
    def get(self, user_id):
        context = self.get_context(user_id)
        return render_template('user/user.html',
                               endpoint='views.user', **context)


class UserOverviewView(UserMixin, MethodView):
    def get(self, user_id):
        context = self.get_context(user_id)
        days = self.worktimes.with_entities(Worktime.day).distinct()

        data = [(d[0], self.worktimes.filter_by(day=d[0])) for d in days]

        total = sum([wt.hours or 0 for wt in self.worktimes])
        return render_template('user/overview.html',
                               days=days, data=data,
                               endpoint='views.user-overview',
                               **context)


class UserSummaryView(UserMixin, MethodView):
    def get(self, user_id):
        context = self.get_context(user_id)

        projects = set([wt.project for wt in self.worktimes])
        data = [
            (p, sum(
                [wt.hours or 0 for wt in self.worktimes.filter_by(project=p)]))
            for p in projects]

        total = sum([wt.hours or 0 for wt in self.worktimes])
        return render_template('user/summary.html', data=data,
                               endpoint='views.user-summary',
                               **context)


# utils
@views.add_app_template_global
def active(text, force=False):
    if text in request.url or force:
        return 'class=active'
    return ''


# urls.py
views.add_url_rule('/', view_func=Homepage.as_view('homepage'))
views.add_url_rule('/project/<project_id>',
                   view_func=ProjectView.as_view('project'))
views.add_url_rule('/project/<project_id>/monthly',
                   view_func=ProjectMonthlyView.as_view('project_monthly'))
views.add_url_rule('/project/all', view_func=ProjectView.as_view('projects'))
views.add_url_rule('/user/all', view_func=UserAll.as_view('users'))
views.add_url_rule('/user/<user_id>/listing',
                   view_func=UserView.as_view('user'))
views.add_url_rule('/user/<user_id>/overview',
                   view_func=UserOverviewView.as_view('user-overview'))
views.add_url_rule('/user/<user_id>/summary',
                   view_func=UserSummaryView.as_view('user-summary'))

