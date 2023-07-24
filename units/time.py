
import datetime

from .errors import UnitExecutionError


def duration_to_string(
    duration: datetime.timedelta,
    weeks: bool = True,
    milliseconds: bool = False,
    microseconds: bool = False,
    abbreviate: bool = False,
    separator: str = ' '
) -> str:
    # TODO: Support colon format
    # TODO: Default output for duration of 0?
    if not isinstance(duration, datetime.timedelta):
        raise UnitExecutionError("duration must be datetime.timedelta")

    negative = False
    if duration.total_seconds() < 0:
        duration = abs(duration)
        negative = True

    units = {"year": duration.days // 365}
    if weeks:
        units["week"] = duration.days % 365 // 7
        units["day"] = duration.days % 365 % 7
    else:
        units["day"] = duration.days % 365
    units["hour"] = duration.seconds // 3600
    units["minute"] = duration.seconds // 60 % 60
    units["second"] = duration.seconds % 60
    if milliseconds:
        units["millisecond"] = duration.microseconds // 1000
        if microseconds:
            units["microsecond"] = duration.microseconds % 1000
    elif microseconds:
        units["microsecond"] = duration.microseconds

    outputs = []
    for name, value in units.items():
        if not value:
            continue
        if negative:
            value = -value
        if abbreviate:
            if name == "millisecond":
                output = f"{value}ms"
            elif name == "microsecond":
                output = f"{value}μs"
            else:
                output = f"{value}{name[0]}"
        else:
            output = f"{value} {name}"
            if abs(value) > 1:
                output += 's'
        outputs.append(output)

    return separator.join(outputs)

