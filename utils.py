from datetime import datetime
from datetime import timedelta
from typing import TypeVar

TIME_FORMAT = "%H:%M:%S"

NO_DURATION = timedelta(hours=0)

T = TypeVar("T")


def optionals(condition: bool, value: list[T]) -> list[T]:
    if condition:
        return value
    else:
        return []


def parse_timedelta(time_string: str) -> timedelta:
    try:
        time = parse_time(time_string)
        delta = timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
    except:
        delta = NO_DURATION

    return delta


def parse_time(time_string: str, strip_milliseconds: bool = False) -> datetime:
    if strip_milliseconds:
        time_string = time_string.split(".", 1)[0]

    return datetime.strptime(time_string, TIME_FORMAT)


def format_time(time: datetime) -> str:
    return time.strftime(TIME_FORMAT)
