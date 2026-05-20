import unittest, os, tempfile
import app as webscraping 

class Tests(unittest.TestCase):
	def setUp(self):
		self.db_fd, webscraping.app.config['DATABASE'] = tempfile.mkstemp()
		webscraping.app.testing = True
		self.app = webscraping.app.test_client()
		with webscraping.app.app_context():
			webscraping.init_db()

	def tearDown(self):
		os.close(self.db_fd)
		os.unlink(webscraping.app.config['DATABASE'])


	"""Bluesky tests."""


	def test_enter_bsky(self):
		"""Enter the site and submit."""
		bluesky = self.app.post('/bluesky', data=dict(
			bluesky_length='5'
		))
		assert bluesky.status_code == 200


	def test_bsky_csv(self):
		"""Enter the site, get a csv, and check to see if it has the right format."""
		# Ensure that there is a csv to analyze. 
		self.app.get('/bluesky', data=dict(
			bluesky_length='5'
		))
		with open(os.path.relpath('../csvfiles/bluesky.csv')) as file:
			text = file.readline()
			# Assert that cells were rendered correctly. 
			for item in text.split(','):
				assert '#' not in item[0], item[len(item)]
			# Assert that there are the correct number of columns inserted.
#			assert len(text.split(',')) == 5 

	def test_required_bluesky_0(self):
		"""Ensure that it is required to enter `bluesky_length`."""
		bluesky = self.app.get('/bluesky', data=dict())
		assert bluesky.status_code != 200		

	"""X tests."""

	def test_enter_x(self):
		"""Ensure we can enter the page and submit the data."""
		x = self.app.post('/x', data=dict(
			x_length='5'
		))
		assert x.status_code == 200

	def test_required_x_0(self):
		"""Ensure that it is required to enter `x_length`."""
		x = self.app.get('/x', data=dict())
		assert x.status_code != 200	

	"""Pornhub tests."""

	def test_enter_pornhub_0(self):
		"""Enter pornhub without entering tags or pornstars."""
		pornhub = self.app.post('/pornhub', data=dict(
			pornhub_length='5'
		))
		assert pornhub.status_code == 200

	def test_enter_pornhub_1(self):
		"""Enter pornhub by entering tags, not pornstars."""
		pornhub = self.app.post('/pornhub', data=dict(
			pornhub_length='5',
			tags=['oiled']
		))
		assert pornhub.status_code == 200

	def test_enter_pornhub_2(self):
		"""Enter pornhub by entering tags and pornstars."""
		pornhub = self.app.post('/pornhub', data=dict(
			pornhub_length='5',
			tags=['cum'],
			pornstars=['Evie Christian']
		))
		assert pornhub.status_code == 200

	def test_required_pornhub_0(self):
		"""Entering `pornhub_length` should be required to submit the form."""
		pornhub = self.app.get('/pornhub', data=dict())
		assert pornhub.status_code != 200


if __name__ == "__main__":
	unittest.main()