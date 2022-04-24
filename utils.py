from datetime import datetime
from datetime import timedelta

TIME_FORMAT = "%H:%M:%S"

NO_DURATION = timedelta(hours=0)


def parse_timedelta(time_string):
    try:
        time = parse_time(time_string)
        delta = timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
    except:
        delta = NO_DURATION

    return delta


def parse_time(time_string, strip_milliseconds=False):
    if strip_milliseconds:
        time_string = time_string.split(".", 1)[0]

    return datetime.strptime(time_string, TIME_FORMAT)


def format_time(time):
    return time.strftime(TIME_FORMAT)
