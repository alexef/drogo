from datetime import datetime
from icalendar import Calendar
import re
from drogo.models import get_projects


def parse_event(component):
    return {
        'modified': component['last-modified'].dt,
        'start': component['dtstart'].dt,
        'end': component['dtend'].dt,
        'summary': unicode(component['summary']),
        'uid': component['uid'],
    }


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

    hours = re.findall(r'([0-9]+\.?[0-9]*)[oh]', summary)
    if hours:
        worktime.hours = float(hours[0])

    project_names = get_projects()
    for word in summary.lower().split(' '):
        if word in project_names:
            worktime.project = project_names[word]
            break

    return worktime
