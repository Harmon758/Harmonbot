
import unittest

from hypothesis import given
from hypothesis.strategies import floats, uuids

from units.location import wind_degrees_to_direction
from units.errors import UnitExecutionError

class TestWindDegreesToDirection(unittest.TestCase):
	
	@given(uuids())
	def test_invalid_degrees_type(self, degrees):
		self.assertRaises(UnitExecutionError, wind_degrees_to_direction, degrees)
	
	@given(floats(max_value = 0, exclude_max = True))
	def test_negative_degrees(self, degrees):
		self.assertRaises(UnitExecutionError, wind_degrees_to_direction, degrees)
	
	@given(floats(min_value = 360, exclude_min = True))
	def test_degrees_greater_than_360(self, degrees):
		self.assertRaises(UnitExecutionError, wind_degrees_to_direction, degrees)
	
	@given(floats(min_value = 0, max_value = 360))
	def test_output_type(self, degrees):
		self.assertIsInstance(wind_degrees_to_direction(degrees), str)
	
	@given(floats(min_value = 0, max_value = 11.25))
	def test_low_n_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), 'N')
	
	@given(floats(min_value = 348.75, max_value = 360))
	def test_high_n_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), 'N')
	
	@given(floats(min_value = 33.75, max_value = 56.25, exclude_min = True))
	def test_ne_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "NE")
	
	@given(floats(min_value = 56.25, max_value = 78.75, exclude_min = True))
	def test_ene_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "ENE")
	
	@given(floats(min_value = 78.75, max_value = 101.25, exclude_min = True))
	def test_e_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), 'E')
	
	@given(floats(min_value = 101.25, max_value = 123.75, exclude_min = True))
	def test_ese_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "ESE")
	
	@given(floats(min_value = 123.75, max_value = 146.25, exclude_min = True))
	def test_se_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "SE")
	
	@given(floats(min_value = 146.25, max_value = 168.75, exclude_min = True))
	def test_sse_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "SSE")
	
	@given(floats(min_value = 168.75, max_value = 191.25, exclude_min = True))
	def test_s_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), 'S')
	
	@given(floats(min_value = 191.25, max_value = 213.75, exclude_min = True))
	def test_ssw_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "SSW")
	
	@given(floats(min_value = 213.75, max_value = 236.25, exclude_min = True))
	def test_sw_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "SW")
	
	@given(floats(min_value = 236.25, max_value = 258.75, exclude_min = True))
	def test_wsw_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "WSW")
	
	@given(floats(min_value = 258.75, max_value = 281.25, exclude_min = True))
	def test_w_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), 'W')
	
	@given(floats(min_value = 281.25, max_value = 303.75, exclude_min = True))
	def test_wnw_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "WNW")
	
	@given(floats(min_value = 303.75, max_value = 326.25, exclude_min = True))
	def test_nw_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "NW")
	
	@given(floats(
		min_value = 326.25, max_value = 348.75,
		exclude_min = True, exclude_max = True
	))
	def test_nnw_output(self, degrees):
		self.assertEqual(wind_degrees_to_direction(degrees), "NNW")

if __name__ == "__main__":
	unittest.main()
