
import unittest

from datetime import timedelta

from hypothesis import assume, given
from hypothesis.strategies import timedeltas, times

from units.time import duration_to_string


class TestDurationToString(unittest.TestCase):

    @given(times())
    def test_invalid_duration_type(self, duration):
        with self.assertRaises(TypeError):
            duration_to_string(duration)

    @given(timedeltas())
    def test_output_type(self, duration):
        assert isinstance(duration_to_string(duration), str)

    @given(timedeltas(min_value = timedelta(days = 365)))
    def test_year_output(self, duration):
        assert "year" in duration_to_string(duration)

    @given(timedeltas(min_value = timedelta(days = 7)))
    def test_week_output(self, duration):
        output = duration_to_string(duration, weeks = True)
        if duration.days % 365 >= 7:
            assert "week" in output
        else:
            assert "week" not in output

    @given(timedeltas(min_value = timedelta()))
    def test_day_without_week_output(self, duration):
        output = duration_to_string(duration, weeks = False)
        if duration.days % 365:
            assert "day" in output
        else:
            assert "day" not in output

    @given(timedeltas(min_value = timedelta()))
    def test_day_with_week_output(self, duration):
        output = duration_to_string(duration, weeks = True)
        if duration.days % 365 % 7:
            assert "day" in output
        else:
            assert "day" not in output

    @given(timedeltas(min_value = timedelta()))
    def test_hour_output(self, duration):
        output = duration_to_string(duration)
        if duration.seconds >= 3600:
            assert "hour" in output
        else:
            assert "hour" not in output

    @given(timedeltas(min_value = timedelta()))
    def test_minute_output(self, duration):
        output = duration_to_string(duration)
        if duration.seconds % 3600 >= 60:
            assert "minute" in output
        else:
            assert "minute" not in output

    @given(timedeltas(min_value = timedelta()))
    def test_second_output(self, duration):
        output = duration_to_string(duration)
        if duration.seconds % 60:
            assert " second" in output
        else:
            assert " second" not in output

    @given(timedeltas(min_value = timedelta()))
    def test_millisecond_output(self, duration):
        output = duration_to_string(duration, milliseconds = True)
        if duration.microseconds >= 1000:
            assert "millisecond" in output
        else:
            assert "millisecond" not in output

    @given(timedeltas())
    def test_microsecond_without_millisecond_output(self, duration):
        output = duration_to_string(duration, microseconds = True)
        if duration.microseconds:
            assert "microsecond" in output
        else:
            assert "microsecond" not in output

    @given(timedeltas())
    def test_microsecond_with_millisecond_output(self, duration):
        output = duration_to_string(
            duration, milliseconds = True, microseconds = True
        )
        if duration.microseconds % 1000:
            assert "microsecond" in output
        else:
            assert "microsecond" not in output

    @given(timedeltas())
    def test_abbreviations(self, duration):
        output = duration_to_string(
            duration, abbreviate = True,
            milliseconds = True, microseconds = True,
            separator = '|'
        )
        assume(output)
        for unit in output.split('|'):
            if unit.endswith(("ms", "μs")):
                assert unit[:-2].lstrip('-').isdecimal()
            else:
                assert unit[:-1].lstrip('-').isdecimal()
                assert unit[-1].isalpha()

    @given(timedeltas(max_value = timedelta(microseconds = -1)))
    def test_negative_duration(self, duration):
        output = duration_to_string(duration, separator = '|')
        for unit in output.split('|'):
            assert unit.startswith('-')
        # TODO: Check output correctness

    @given(timedeltas())
    def test_unit_plurality(self, duration):
        output = duration_to_string(duration, separator = '|')
        assume(output)
        for section in output.split('|'):
            value, unit = section.split(' ')
            if abs(int(value)) > 1:
                assert unit.endswith('s')
            else:
                assert not unit.endswith('s')


if __name__ == "__main__":
    unittest.main()

