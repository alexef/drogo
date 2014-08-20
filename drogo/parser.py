from datetime import datetime
import logging
from icalendar import Calendar
import re
from drogo.models import get_projects
from drogo.utils import naive


def parse_summary_text(summary):
    info = {}
    hours = re.findall(r'([0-9]+\.?[0-9]*)\ *[oh][rae]*', summary)
    if hours:
        info['hours'] = float(hours[0])
    else:
        info['hours'] = None
    return info


def parse_event(component):
    try:
        info = parse_summary_text(unicode(component['summary']))
        return {
            'modified': naive(component['last-modified'].dt),
            'start': naive(component['dtstart'].dt),
            'end': naive(component['dtend'].dt),
            'summary': unicode(component['summary']),
            'uid': component['uid'],
            'hours': info['hours'],
        }
    except Exception as e:
        logging.exception(e)
        return {}


def parse_ical(ical_text):
    gcal = Calendar.from_ical(ical_text)
    for c in gcal.walk():
        if c.name == 'VEVENT':
            yield parse_event(c)


def parse_summary(worktime):
    if not worktime.event:
        return worktime
    summary = worktime.event.summary

    worktime.details = summary
    if isinstance(worktime.event.start, datetime):
        worktime.day = worktime.event.start.date()
    else:
        worktime.day = worktime.event.start

    if worktime.event.hours is not None:
        worktime.hours = worktime.event.hours

    project_names = get_projects()
    summary_low = summary.lower()

    project_names_extended = filter(lambda s: ' ' in s, project_names)
    project_names_simple = filter(lambda s: ' ' not in s, project_names)
    for name in project_names_extended:
        if name in summary_low:
            worktime.project = project_names[name]
            break

    for word in summary_low.split(' '):
        if word in project_names_simple:
            worktime.project = project_names[word]
            break

    return worktime
