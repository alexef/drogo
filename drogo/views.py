from datetime import date, datetime
from flask import Blueprint, current_app
from flask.views import MethodView
from flask import render_template, request, redirect, flash, url_for, session
from flask.ext.login import login_user, login_required, logout_user
from flask.ext.principal import Principal, Identity, AnonymousIdentity, \
     identity_changed
from travispy import TravisPy
from drogo.models import Project, User, Worktime
from drogo.utils import get_total_days, get_end_day, get_all_projects
from drogo.forms import LoginForm
from drogo.auth import ldap_fetch


views = Blueprint('views', __name__)


class Homepage(MethodView):
    def get(self):
        return render_template('homepage.html', users=User.query.count(),
                               projects=get_all_projects().count())


class Dashboard(MethodView):
    @login_required
    def get(self):
        projects = list(get_all_projects())
        travis = TravisPy.github_auth(current_app.config['TRAVIS_API_KEY'])
        for p in projects:
            if p.github_slug:
                p.travis = travis.repo(p.github_slug)
            else:
                p.travis = {}
        return render_template('dashboard.html', projects=projects)


class ProjectView(MethodView):
    @login_required
    def get(self, project_id=None):
        project = project_id and Project.query.get(project_id)
        projects = Project.query.order_by(Project.slug)
        return render_template('project.html', project=project,
                               projects=projects)


class ProjectMonthlyView(MethodView):
    @login_required
    def get(self, project_id):
        project = Project.query.get_or_404(project_id)
        projects = Project.query.order_by(Project.slug)
        month = request.args.get('month')
        worktimes = project.month_worktimes(month)
        return render_template('project_month.html', project=project,
                               projects=projects, month=month,
                               worktimes=worktimes)


class UserAll(MethodView):
    @login_required
    def get(self):
        print
        return render_template('user/user.html', user=None,
                               users=User.query.all())


class UserMixin(object):
    def get_times(self, day):
        return [wt for wt in self.worktimes if wt.day == day]

    def get_hours(self, project):
        return sum([wt.hours or 0 for wt in
                    self.worktimes if wt.project == project])

    def get_tickets(self, project):
        tickets = []
        for wt in self.worktimes:
            if wt.project == project:
                tickets += [tw.ticket for tw in wt.tickets]
        return set(tickets)

    @login_required
    def get_context(self, user_id):
        self.month = request.args.get('month', date.today().strftime("%Y-%m"))
        self.user = User.query.get_or_404(user_id)
        self.worktimes = self.user.month_worktimes(self.month)

        total, days_computed = get_total_days(self.worktimes)
        return {
            'users': User.query.all(),
            'month': self.month,
            'user': self.user,
            'worktimes': self.worktimes,
            'total': total,
            'days_computed': days_computed,
        }


class UserView(UserMixin, MethodView):
    @login_required
    def get(self, user_id):
        context = self.get_context(user_id)
        return render_template('user/user.html',
                               endpoint='views.user', **context)


class PerdayView(UserView):
    @login_required
    def get(self, user_id):
        context = self.get_context(user_id)
        days = set([wt.day for wt in self.worktimes])
        days_data = []
        for day in days:
            day_data = {}
            wts = self.get_times(day)
            for wt in wts:
                if not wt.project or wt.project.unpaid:
                    continue
                day_data.setdefault(wt.project, {'hours': 0, 'tickets': []})
                day_data[wt.project]['hours'] += wt.hours
                day_data[wt.project]['tickets'] += [
                    t.ticket for t in wt.tickets
                ]
            if day_data:
                days_data.append({'day': day, 'projects': day_data})
        days_data.sort(key=lambda s: s['day'])
        return render_template('user/perday.html',
                               endpoint='views.user', days=days_data,
                               **context)


class UserOverviewView(UserMixin, MethodView):
    @login_required
    def get(self, user_id):
        context = self.get_context(user_id)
        days = self.worktimes.with_entities(Worktime.day).distinct()

        data = dict(
            [(d[0].day, self.worktimes.filter_by(day=d[0])) for d in days])

        month = datetime.strptime(self.month + '-01', '%Y-%m-%d')
        end_day = get_end_day(month)
        first_day = int(month.strftime('%w'))
        curday = (first_day + 6) % 7
        return render_template('user/overview.html',
                               days=days, data=data, curday=curday,
                               end_day=end_day,
                               endpoint='views.user-overview',
                               **context)


class UserSummaryView(UserMixin, MethodView):
    @login_required
    def get(self, user_id):
        context = self.get_context(user_id)

        projects = set([wt.project for wt in self.worktimes if wt.project])
        data = [(p, self.get_hours(p), self.get_tickets(p)) for p in projects]
        data.sort(key=lambda s: (s[0] and s[0].free) or -s[1])

        return render_template('user/summary.html', data=data,
                               endpoint='views.user-summary',
                               **context)

# utils
@views.add_app_template_global
def active(text, force=False):
    if text in request.url or force:
        return 'class=active'
    return ''


#login misc
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate():
            user = ldap_fetch(name=form.username.data,
                              passwd=form.password.data)
            if user and user.active is not False:
                login_user(user)
                identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))
                return redirect(url_for('.user-overview', user_id=user.id))
        else:
            flash("Username or password incorrect :(")
    return render_template("login.html", form=form)


@login_required
def logout():
    logout_user()
    #clean session
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    return redirect(url_for('.homepage'))


# urls.py
views.add_url_rule('/', view_func=Homepage.as_view('homepage'))
views.add_url_rule('/dashboard', view_func=Dashboard.as_view('dashboard'))
views.add_url_rule('/project/<project_id>',
                   view_func=ProjectView.as_view('project'))
views.add_url_rule('/project/<project_id>/monthly',
                   view_func=ProjectMonthlyView.as_view('project_monthly'))
views.add_url_rule('/project/all',
                   view_func=ProjectView.as_view('projects'))
views.add_url_rule('/user/all', view_func=UserAll.as_view('users'))
views.add_url_rule('/user/<user_id>/listing',
                   view_func=UserView.as_view('user'))
views.add_url_rule('/user/<user_id>/overview',
                   view_func=UserOverviewView.as_view('user-overview'))
views.add_url_rule('/user/<user_id>/summary',
                   view_func=UserSummaryView.as_view('user-summary'))
views.add_url_rule('/user/<user_id>/perday',
                   view_func=PerdayView.as_view('perday'))
views.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
views.add_url_rule('/logout', view_func=logout)
