from datetime import datetime
from flask.ext.script import Manager
import requests
from drogo.models import db, Event, Worktime, User, Project, get_projects
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
    event_obj = (
        Event.query.filter_by(uid=event['uid']).first() or Event(**event)
    )
    if event['modified'] != absolute(event_obj.modified):
        event_obj.modified = event['modified']
        event_obj.summary = event['summary']
        event_obj.start = event['start']
        event_obj.end = event['end']
    db.session.add(event_obj)

    work_time_obj = (
        event_obj.worktime or Worktime(event=event_obj, user_id=userid)
    )
    parse_summary(work_time_obj)
    db.session.add(work_time_obj)
    print u"Added {0}".format(work_time_obj.details)


@db_manager.command
def init():
    db.create_all()
    db.session.add(User(id=1))
    db.session.commit()


@user_manager.command
def list():
    for user in User.query.all():
        print "{id} {full_name} {calendar}".format(id=user.id,
                                                   full_name=user.full_name,
                                                   calendar=user.calendar_url)


@user_manager.command
def mod(userid):
    user = User.query.get(userid)
    name = raw_input("Full Name (enter for unchanged):")
    if name:
        user.full_name = name
    cal = raw_input("Calendar URL (enter for unchanged):")
    if cal:
        user.calendar_url = cal
    db.session.commit()
    print "updated."


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
        print "User: ", user.id
        for wt in user.worktimes:
            print " ", wt.day, wt.details, wt.hours, "hours", unicode(
                wt.project)


@work_manager.command
def list_project(slug):
    projects = get_projects()
    project_obj = projects.get(slug)
    if not project_obj:
        print "No project with this name."
    else:
        total = 0
        for wt in project_obj.worktimes:
            print " ", wt.day, wt.details, wt.hours, "hours", unicode(
                wt.project)
            if wt.hours:
                total += wt.hours
        print "Total: ", total, "hours"


@work_manager.command
def project(slug, alias=None):
    proj_obj = Project.query.filter_by(slug=slug).first() or Project(slug=slug)
    db.session.add(proj_obj)
    db.session.commit()

    if alias is not None:
        proj_obj.add_alias(alias)


@work_manager.command
def update_all():
    """ Update all user calendars """
    for user in User.query.all():
        if not user.calendar_url:
            continue

        resp = requests.get(user.calendar_url)
        if resp.status_code != 200:
            print "Failed to get calendar feed. (response: {0}".format(
                resp.status_code)
        else:
            events = parse_ical(resp.content)
            for event in events:
                add_event(event, user.id)
    db.session.commit()
