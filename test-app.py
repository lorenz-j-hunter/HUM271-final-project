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

	def test_enter_bsky(self):
		bluesky = self.app.post('/bluesky', data=dict(
			bluesky_length='5'
		))
		assert bluesky.status_code == 200

	def test_enter_x(self):
		x = self.app.post('/x', data=dict(
			x_length='5'
		))
		assert x.status_code == 200

	def test_enter_pornhub_0(self):
		"""Enter pornhub without entering tags or pornstars."""
		pornhub = self.app.post('/pornhub', data=dict(
			pornhub_length='5'
		))
		assert pornhub.status_code == 200

if __name__ == "__main__":
	unittest.main()