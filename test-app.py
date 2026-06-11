import unittest, os, tempfile
import app as webscraping 
from time import perf_counter_ns

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
				assert '(' not in item[0], item[len(item)]
				assert ')' not in item[0], item[len(item)]
			# Assert that there are the correct number of columns inserted.
			assert len(text.split(',')) == 5
		with webscraping.app.app_context():
			db = webscraping.get_db()
			# Ensure that database data for all columns is there.
			cur = db.execute('SELECT * FROM first_dim_for_bluesky')
			f = cur.fetchall()
			item_ids = [row[0] for row in f]
			names = [row[1] for row in f]
			dids = [row[2] for row in f]
			ages = [row[3] for row in f]
			pronouns = [row[4] for row in f]
			assert len(item_ids) == len(names) == len(dids) == len(ages) == len(pronouns)

	def test_r(self):
		"""Ensure that it is required to enter `bluesky_length` and
		`max_events`-`type`."""
		bluesky = self.app.get('/bluesky', data=dict())
		assert bluesky.status_code != 200

	def test_j(self):
		"""Ensure that `max_events`-`type` and `bluesky_length` entry returns 
		a 200 response."""
		bluesky = self.app.get('/bluesky', data=dict({
			'bluesky_length': '5'
		}))
		assert bluesky.status_code == 200
		bluesky = self.app.get('/bluesky', data=dict({
			'max_events': '5',
			'type': 'post'
		}))
		assert bluesky.status_code == 200

	def test_r_gothru(self, age: str | None ='yes', pronouns: str | None ='yes', limit: str | None='5'):
		"""Go through REST bluesky, to ctrl, to final"""
		self.app.post('/bluesky', data=dict({
			'bluesky_length': '5'
		}))
		self.app.post('/bluesky_r_ctrl', data=dict({
			'age': age,
			'pronouns': pronouns,
			'limit': limit 
		}))
		self.app.get('/bluesky_r_final', data=dict({'pronouns': 'yes'}))

	def test_j_gothru(self, max_events='5', type='post', querystring='a', mark_blocks: str | None='yes'):
		"""Go through jetstream bluesky, to ctrl, to final"""
		self.app.post('/bluesky', data=dict({
			'max_events': max_events,
			'type': type 
		}))
		if type == 'post':
			self.app.post('/bluesky_j_ctrl', data=dict({
				'querystring': querystring 
			}))
		elif type == 'follow':
			self.app.post('/bluesky_j_ctrl', data=dict({
				'mark-blocks':  mark_blocks
			}))
		self.app.get('/bluesky_j_final', data=dict({'pronouns': 'yes'}))

	def test_r_goback(self, age: str | None='yes', pronouns: str | None='yes', limit: str | None ='5'):
		"""Begin at REST final, then go back and resubmit"""
		self.app.post('/bluesky_r_ctrl', data=dict({
			'age': age,
			'pronouns': pronouns,
			'limit': limit 
		}))
		self.app.post('/bluesky_r_final', data=dict())
		self.app.post('/bluesky_r_ctrl', data=dict({
			'age': age,
			'pronouns': pronouns,
			'limit': limit 
		}))
		self.app.post('/bluesky_r_final', data=dict())

	def test_j_goback(self, max_events='5', type='post', querystring='a', mark_blocks: str | None='yes'):
		"""Begin at jetstream final, then go back and resubmit"""
		# bluesky
		self.app.post('/bluesky', data=dict({
			'max_events': max_events,
			'type': type 
		}))
		# ctrl
		if type == 'post':
			self.app.post('/bluesky_j_ctrl', data=dict({
				'querystring': querystring 
			}))
		elif type == 'follow':
			self.app.post('/bluesky_j_ctrl', data=dict({
				'mark-blocks': mark_blocks
			}))
		# final
		self.app.post('/bluesky_j_final', data=dict())
	  # back (ctrl)
		if type == 'post':
			self.app.post('/bluesky_j_ctrl', data=dict({
				'querystring': querystring 
			}))
		elif type == 'follow':
			self.app.post('/bluesky_j_ctrl', data=dict({
				'mark-blocks': mark_blocks
			}))
		# final
		self.app.post('/bluesky_j_final', data=dict())

	def test_r_tomain(self, bluesky_length: str = '5', age='yes', pronouns='yes', limit: str | None='5'):
		"""Begin at REST final, then go to main and resubmit"""
		self.app.post('/bluesky_r_ctrl', data=dict({
			'age': age,
			'pronouns': pronouns,
			'limit': limit 
		}))
		self.app.post('/bluesky_r_final', data=dict())
		self.app.post('/', data=dict())
		self.app.post('/bluesky', data=dict({
			'bluesky_length': bluesky_length 
		}))
		self.app.post('/bluesky_r_ctrl', data=dict({
			'age': age,
			'pronouns': pronouns,
			'limit': limit 
		}))
		self.app.post('/bluesky_r_final', data=dict())

	def test_j_tomain(self, max_events='5', type='post', querystring='a', mark_blocks: str | None='yes'):
		"""Begin at jetstream final, then go to main and resubmit"""
		# final
		self.app.post('/bluesky_j_final', data=dict())
		# main
		self.app.post('/', data=dict())
		# bluesky
		self.app.post('/bluesky', data=dict({
			'max_events': max_events,
			'type': type 
		}))
		# ctrl
		if type == 'post':
			self.app.post('/bluesky_j_ctrl', data=dict({
				'querystring': querystring 
			}))
		elif type == 'follow':
			self.app.post('/bluesky_j_ctrl', data=dict({
				'mark-blocks': mark_blocks
			}))
		# final
		self.app.post('/bluesky_j_final', data=dict())

	def test_r_dontshow(self):
		"""If we don't select the columns, they shouldn't appear in the csv"""
		# we selected neither column.
		self.test_r_gothru(age=None, pronouns=None)
		with open(os.path.relpath('../csvfiles/bluesky.csv')) as file:
			text = file.readline()
			# assert that these unselected cols aren't in the csv.
			assert len(text.split(',')) == 3
		self.test_r_gothru(age=None, pronouns='yes')
		with open(os.path.relpath('../csvfiles/bluesky.csv')) as file:
			text = file.readline()
			# assert that these unselected cols aren't in the csv.
			assert len(text.split(',')) == 4
		self.test_r_gothru(age='yes', pronouns='yes')
		with open(os.path.relpath('../csvfiles/bluesky.csv')) as file:
			text = file.readline()
			# assert that all cols are in csv 
			assert len(text.split(',')) == 5

	def test_j_dontshow(self):
		"""If we don't select the columns, they shouldn't appear in the csv.
		Also, tests querystring"""
		# querystring
		self.test_j_gothru(type='post', querystring='a')
		with open(os.path.relpath('../csvfiles/bluesky-jetstream.csv')) as file:
			while file.readline():
				text = file.readline()
				assert 'a' in text.split(',')[1]
		# columns
		self.test_j_gothru(type='follow', mark_blocks=None)
		with open(os.path.relpath('../csvfiles/bluesky-jetstream.csv')) as file:
			text = file.readline()
			assert len(text.split(',')) == 3 
		self.test_j_gothru(type='follow', mark_blocks='yes')
		with open(os.path.relpath('../csvfiles/bluesky-jetstream.csv')) as file:
			text = file.readline()
			assert len(text.split(',')) == 4 

	def test_r_time(self):
		"""Ensure that it doesn't take too long to create the csv."""
		start = perf_counter_ns()
		self.test_r_gothru(age=None, pronouns=None)	
		end = perf_counter_ns()
		duration = ((end - start) * (10**9)) / 1000 # in seconds
		assert duration < 3 # takes less than three seconds to complete 5-row csv.

	def test_j_time(self):
		"""Ensure that it doesn't take too long to create the csv."""
		start = perf_counter_ns()
		self.test_j_gothru(type='post', querystring='a')
		end = perf_counter_ns()
		duration = ((end - start) * (10**9)) / 1000 # in seconds
		assert duration < 1 # takes less than three seconds to complete 5-row csv.


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

	def test_x_csv(self):
		"""Make sure the csv and database of X are proper."""
		# Ensure that there is a csv to analyze. 
		self.app.get('/x', data=dict(
			x_length='5'
		))
		with open(os.path.relpath('../csvfiles/x.csv')) as file:
			text = file.readline()
			# Assert that cells were rendered correctly. 
			for item in text.split(','):
				assert '#' not in item[0], item[len(item)]
				assert '(' not in item[0], item[len(item)]
				assert ')' not in item[0], item[len(item)]
			# Assert that there are the correct number of columns inserted.
#			assert len(text.split(',')) == 6 
		with webscraping.app.app_context():
			db = webscraping.get_db()
			# Ensure that database data for all columns is there.
			cur = db.execute('SELECT * FROM first_dim_for_x')
			f = cur.fetchall()
			names = [row[0] for row in f]
			account_ages = [row[1] for row in f]
			affiliations = [row[2] for row in f]
			verified = [row[3] for row in f]
			assert len(names) == len(account_ages) == len(affiliations) == len(verified)


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

	def test_pornhub_csv(self):
		"""Enter the site, get a csv, and check to see if it has the right format."""
		# Ensure that there is a csv to analyze. 
		self.app.get('/pornhub', data=dict(
			pornhub_length='5',
			pornstar='Lily Slutty'
		))
		with open(os.path.relpath('../csvfiles/pornhub.csv')) as file:
			text = file.readline()
			# Assert that cells were rendered correctly. 
			for item in text.split(','):
				assert '#' not in item[0], item[len(item)]
				assert '(' not in item[0], item[len(item)]
				assert ')' not in item[0], item[len(item)]
			# Assert that there are the correct number of columns inserted.
			assert len(text.split(',')) == 6 
		with webscraping.app.app_context():
			db = webscraping.get_db()
			# Ensure that database data for all columns is there.
			cur = db.execute('SELECT * FROM first_dim_for_pornhub')
			f = cur.fetchall()
			item_ids = [row[0] for row in f]
			titles = [row[1] for row in f]
			pornstars = [row[2] for row in f]
			views = [row[3] for row in f]
			ratings = [row[4] for row in f]
			assert len(item_ids) == len(titles) == len(pornstars) == len(views) == len(ratings)

	def test_required_pornhub_0(self):
		"""Entering `pornhub_length` should be required to submit the form."""
		pornhub = self.app.get('/pornhub', data=dict())
		assert pornhub.status_code != 200


if __name__ == "__main__":
	unittest.main()