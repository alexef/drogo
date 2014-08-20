from datetime import datetime, timedelta
import pytz


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
