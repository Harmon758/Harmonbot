
import unittest

from datetime import timedelta

from hypothesis import assume, given
from hypothesis.strategies import timedeltas, times

from units.time import duration_to_string
from units.errors import UnitExecutionError

class TestDurationToString(unittest.TestCase):
	
	@given(times())
	def test_invalid_duration_type(self, duration):
		self.assertRaises(UnitExecutionError, duration_to_string, duration)
	
	@given(timedeltas())
	def test_output_type(self, duration):
		self.assertIsInstance(duration_to_string(duration), str)
	
	@given(timedeltas(min_value = timedelta(days = 365)))
	def test_year_output(self, duration):
		self.assertIn("year", duration_to_string(duration))
	
	@given(timedeltas(min_value = timedelta(days = 7)))
	def test_week_output(self, duration):
		output = duration_to_string(duration, weeks = True)
		if duration.days % 365 >= 7:
			self.assertIn("week", output)
		else:
			self.assertNotIn("week", output)
	
	@given(timedeltas(min_value = timedelta()))
	def test_day_without_week_output(self, duration):
		output = duration_to_string(duration, weeks = False)
		if duration.days % 365:
			self.assertIn("day", output)
		else:
			self.assertNotIn("day", output)
	
	@given(timedeltas(min_value = timedelta()))
	def test_day_with_week_output(self, duration):
		output = duration_to_string(duration, weeks = True)
		if duration.days % 365 % 7:
			self.assertIn("day", output)
		else:
			self.assertNotIn("day", output)
	
	@given(timedeltas(min_value = timedelta()))
	def test_hour_output(self, duration):
		output = duration_to_string(duration)
		if duration.seconds >= 3600:
			self.assertIn("hour", output)
		else:
			self.assertNotIn("hour", output)
	
	@given(timedeltas(min_value = timedelta()))
	def test_minute_output(self, duration):
		output = duration_to_string(duration)
		if duration.seconds % 3600 >= 60:
			self.assertIn("minute", output)
		else:
			self.assertNotIn("minute", output)
	
	@given(timedeltas(min_value = timedelta()))
	def test_second_output(self, duration):
		output = duration_to_string(duration)
		if duration.seconds % 60:
			self.assertIn(" second", output)
		else:
			self.assertNotIn(" second", output)
	
	@given(timedeltas(min_value = timedelta()))
	def test_millisecond_output(self, duration):
		output = duration_to_string(duration, milliseconds = True)
		if duration.microseconds >= 1000:
			self.assertIn("millisecond", output)
		else:
			self.assertNotIn("millisecond", output)
	
	@given(timedeltas())
	def test_microsecond_without_millisecond_output(self, duration):
		output = duration_to_string(duration, microseconds = True)
		if duration.microseconds:
			self.assertIn("microsecond", output)
		else:
			self.assertNotIn("microsecond", output)
	
	@given(timedeltas())
	def test_microsecond_with_millisecond_output(self, duration):
		output = duration_to_string(duration, milliseconds = True, 
									microseconds = True)
		if duration.microseconds % 1000:
			self.assertIn("microsecond", output)
		else:
			self.assertNotIn("microsecond", output)
	
	@given(timedeltas())
	def test_abbreviations(self, duration):
		output = duration_to_string(duration, abbreviate = True, 
									milliseconds = True, microseconds = True, 
									separator = '|')
		assume(output)
		for unit in output.split('|'):
			if unit.endswith(("ms", "μs")):
				self.assertTrue(unit[:-2].lstrip('-').isdecimal())
			else:
				self.assertTrue(unit[:-1].lstrip('-').isdecimal())
				self.assertTrue(unit[-1].isalpha())
	
	@given(timedeltas(max_value = timedelta(microseconds = -1)))
	def test_negative_duration(self, duration):
		output = duration_to_string(duration, separator = '|')
		for unit in output.split('|'):
			self.assertTrue(unit.startswith('-'))
		# TODO: Check output correctness
	
	@given(timedeltas())
	def test_unit_plurality(self, duration):
		output = duration_to_string(duration, separator = '|')
		assume(output)
		for section in output.split('|'):
			value, unit = section.split(' ')
			if abs(int(value)) > 1:
				self.assertTrue(unit.endswith('s'))
			else:
				self.assertFalse(unit.endswith('s'))

if __name__ == "__main__":
	unittest.main()
