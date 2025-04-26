from datetime import timedelta
from typing import TypeVar

T = TypeVar("T")


def optionals(condition: bool, value: list[T]) -> list[T]:
    if condition:
        return value
    else:
        return []


def parse_time(time_string: str, strip_milliseconds: bool = False) -> timedelta:
    if strip_milliseconds:
        time_string = time_string.split(".", 1)[0]

    h, m, s = map(int, time_string.split(":"))

    return timedelta(hours=h, minutes=m, seconds=s)


def format_time(time: timedelta) -> str:
    total_hours = time.days * 24 + time.seconds // 3600
    minutes = (time.seconds % 3600) // 60
    seconds = time.seconds % 60
    return f"{total_hours}:{minutes:02}:{seconds:02}"
