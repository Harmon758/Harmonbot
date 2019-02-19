
import datetime

from .errors import UnitExecutionError

def duration_to_string(duration, weeks = True, milliseconds = False, microseconds = False,
						abbreviate = False, separator = ' '):
	# TODO: Support colon format
	if not isinstance(duration, datetime.timedelta):
		raise UnitExecutionError("duration must be datetime.timedelta")
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
	outputs = []
	for name, value in units.items():
		if not value:
			continue
		if abbreviate:
			if name == "millisecond":
				output = f"{value}ms"
			elif name == "microsecond":
				output = f"{value}μs"
			else:
				output = f"{value}{name[0]}"
		else:
			output = f"{value} {name}"
			if value > 1:
				output += 's'
		outputs.append(output)
	return separator.join(outputs)

