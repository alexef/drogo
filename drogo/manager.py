from datetime import datetime
from flask.ext.script import Manager
import requests
from sqlalchemy import func
from drogo.models import db, Event, Worktime, User, Project, get_projects, \
    Ticket, TicketWorktime
from drogo.parser import parse_ical, parse_summary
from drogo.utils import get_last_week, absolute


db_manager = Manager()
user_manager = Manager()
work_manager = Manager()


def create_manager(app):
    manager = Manager(app)

    manager.add_command('db', db_manager)
    manager.add_command('user', user_manager)
    manager.add_command('work', work_manager)
    return manager


def add_event(event, userid):
    if not event:
        return

    tickets = event.pop('tickets')
    event_obj = (
        Event.query.filter_by(uid=event['uid']).first() or Event(**event)
    )
    if event['modified'] != event_obj.modified:
        event_obj.modified = event['modified']
        event_obj.summary = event['summary']
        event_obj.start = event['start']
        event_obj.end = event['end']
    db.session.add(event_obj)

    work_time_obj = (
        event_obj.worktime or Worktime(event=event_obj, user_id=userid)
    )
    parse_summary(work_time_obj)
    if work_time_obj.project:
        for ticket in tickets:
            ticket_obj = (
                Ticket.query.filter_by(number=ticket,
                                       project=work_time_obj.project).first()
                or Ticket(number=ticket, project=work_time_obj.project)
            )
            db.session.add(ticket_obj)
            t_wt_obj = (
                TicketWorktime.query.filter_by(ticket=ticket_obj,
                                               worktime=work_time_obj).first()
                or TicketWorktime(ticket=ticket_obj, worktime=work_time_obj)
            )
            db.session.add(t_wt_obj)
    db.session.add(work_time_obj)
    return event_obj


def tweak_days(user):
    """ Add days for events without hour information.
    """
    wt_qs = Worktime.query.filter_by(user=user)
    worktimes_nohours = wt_qs.filter(Worktime.event.has(hours=None))
    for wt in worktimes_nohours:
        wt.hours = wt.event.hours
    db.session.commit()
    for wt in worktimes_nohours:
        all_day = (
            wt_qs
            .filter_by(day=wt.day)
            .with_entities(func.sum(Worktime.hours))
            .first()
        )
        all_day = all_day and all_day[0]
        timeleft = 8 - all_day if all_day else 8
        day_noh = worktimes_nohours.filter_by(day=wt.day).count()
        wt.hours = float(timeleft) / day_noh


@db_manager.command
def init():
    db.create_all()
    if not User.query.first():
        db.session.add(User(id=1))
    db.session.commit()


@user_manager.command
def list():
    for user in User.query.all():
        print((
            "{id} {full_name} {calendar} {is_admin}"
            .format(id=user.id,
                    full_name=user.full_name,
                    calendar=user.calendar_url,
                    ldap_username=user.ldap_username,
                    is_admin=user.is_admin)
        ))


@user_manager.command
def mod(userid):
    user = User.query.get(userid)
    name = input("Full Name (enter for unchanged):")
    if name:
        user.full_name = name
    cal = input("Calendar URL (enter for unchanged):")
    if cal:
        user.calendar_url = cal
    ldap_username = input("Ldap username (enter for unchanged):")
    if ldap_username:
        user.ldap_username = ldap_username
    is_admin = input("Admin user y/n (enter for unchanged):")
    if is_admin == 'y':
        user.is_admin = True
    db.session.commit()
    print("updated.")


@work_manager.command
def parse(filename, userid, last_update=None):
    if last_update is None:
        last_update = get_last_week()
    else:
        last_update = absolute(datetime.strptime(last_update, '%Y-%m-%d'))

    with open(filename, 'rb') as fin:
        data = fin.read()
        events = parse_ical(data)
        for event in events:
            if event['modified'] < last_update:
                break
            add_event(event, userid)
    db.session.commit()


@work_manager.command
def list_all():
    for user in User.query.all():
        print("User: ", user.id)
        for wt in user.worktimes:
            print(" ", wt.day, wt.details, wt.hours, "hours", str(
                wt.project))


@work_manager.command
def list_project(slug):
    projects = get_projects()
    project_obj = projects.get(slug)
    if not project_obj:
        print("No project with this name.")
    else:
        total = 0
        for wt in project_obj.worktimes:
            print(" ", wt.day, wt.details, wt.hours, "hours", str(
                wt.project))
            if wt.hours:
                total += wt.hours
        print("Total: ", total, "hours")


@work_manager.command
def project(slug, alias=None, holiday=None, unpaid=None, github_slug=''):
    proj_obj = Project.query.filter_by(slug=slug).first() or Project(slug=slug)
    proj_obj.github_slug = github_slug
    db.session.add(proj_obj)

    if alias is not None:
        proj_obj.add_alias(alias)

    if holiday:
        proj_obj.holiday = holiday == 'True'

    if unpaid:
        proj_obj.unpaid = unpaid == 'True'

    db.session.commit()


@work_manager.command
def update_all():
    """ Update all user calendars """
    all_users = User.query.all()
    for user in all_users:
        if not user.calendar_url:
            continue

        resp = requests.get(user.calendar_url)
        if resp.status_code != 200:
            print("Failed to get calendar feed. (response: {0}".format(
                resp.status_code))
        else:
            print("Fetched", user.calendar_url)
            events = parse_ical(resp.content)
            for event in events:
                add_event(event, user.id)

    db.session.commit()

    for user in all_users:
        tweak_days(user)
    db.session.commit()
