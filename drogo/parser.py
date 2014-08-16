from datetime import datetime
from icalendar import Calendar
import re
from drogo.models import get_projects
from drogo.utils import naive


def parse_event(component):
    return {
        'modified': naive(component['last-modified'].dt),
        'start': naive(component['dtstart'].dt),
        'end': naive(component['dtend'].dt),
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

    hours = re.findall(r'([0-9]+\.?[0-9]*)\ *[oh][rae]*', summary)
    if hours:
        worktime.hours = float(hours[0])

    project_names = get_projects()
    summary_low = summary.lower()
    for name in project_names:
        if name in summary_low:
            worktime.project = project_names[name]
            break

    return worktime
