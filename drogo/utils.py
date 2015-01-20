from datetime import datetime, timedelta
import pytz
from drogo.models import Worktime, Project


def get_last_week():
    start = datetime.now() - timedelta(days=7)
    return absolute(start)


def absolute(dt):
    if dt.tzinfo is None:
        tz = pytz.timezone('Europe/Bucharest')
        return tz.localize(dt)
    return dt


def naive(dt):
    if isinstance(dt, datetime):
        dt = absolute(dt)
        dt = dt.replace(tzinfo=None)
    return dt


def get_distinct_days(wt_qs):
    return wt_qs.with_entities(Worktime.day).distinct()


def get_total_days(worktimes):
    total = sum(
        [wt.hours or 0 for wt in worktimes if not wt.unpaid])
    hours = 0
    distinct_days = get_distinct_days(worktimes)
    for day in distinct_days:
        wts = worktimes.filter_by(day=day[0])
        has_free = False
        for wt in wts:
            if wt.project and (wt.project.holiday or wt.project.unpaid):
                has_free = True
        if not has_free:
            hours += 8
        else:
            hours += sum([wt.hours for wt in wts if wt.paid])

    return total, hours / 8


def get_end_day(month):
    if month.month == 12:
        return 31
    day = month.replace(month=month.month + 1) - timedelta(days=1)
    return int(day.strftime('%d'))


def get_all_projects():
    return Project.query.filter_by(holiday=False, unpaid=False)
