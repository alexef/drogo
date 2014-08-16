from datetime import datetime, timedelta
import pytz


def get_last_week():
    start = datetime.now() - timedelta(days=7)
    return pytz.utc.localize(start)


def absolute(datetime):
    if datetime.tzinfo is None:
        return pytz.utc.localize(datetime)
    return datetime
