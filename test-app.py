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
		# bluesky
		self.app.post('/bluesky', data=dict({
			'bluesky_length': '5'
		}))
		# ctrl
		with webscraping.app.app_context():
			db = webscraping.get_db()
			if webscraping.isempty():
				db.execute('INSERT INTO args (bluesky_length, querystring, max_events, type, mark_blocks) VALUES (?,?,?,?,?)',
									['5', 'null', 'null', 'null', 'null'])
			# if we are coming backward, we do not have request data. Hence isempty().
			db.commit()
			db.close()
		self.app.post('/bluesky_r_ctrl', data=dict({
			'age': age,
			'pronouns': pronouns,
			'limit': limit 
		}))
		# final
		with webscraping.app.app_context():
			db = webscraping.get_db()
			db.execute('SELECT max_events, type FROM args').fetchall() # there's only ever one row in this db.
			db.close()
		self.app.get('/bluesky_r_final', data=dict({'pronouns': 'yes'}))

	def test_j_gothru(self, max_events='5', type='post', querystring='a', mark_blocks: str | None='yes'):
		"""Go through jetstream bluesky, to ctrl, to final"""
		# bluesky
		self.app.post('/bluesky', data=dict({
			'max_events': max_events,
			'type': type 
		}))
		# ctrl
		if type == 'post':
			with webscraping.app.app_context():
				db = webscraping.get_db()
				if webscraping.isempty():
					db.execute('INSERT INTO args (bluesky_length, querystring, max_events, type, mark_blocks) VALUES (?,?,?,?,?)',
										['null', 'null', max_events, type, 'null'])
				# if we are coming backward, we do not have request data. Hence isempty().
				db.commit()
				db.close()
			self.app.post('/bluesky_j_ctrl', data=dict({
				'querystring': querystring 
			}))
		elif type == 'follow':
			with webscraping.app.app_context():
				db = webscraping.get_db()
				if webscraping.isempty():
					db.execute('INSERT INTO args (bluesky_length, querystring, max_events, type, mark_blocks) VALUES (?,?,?,?,?)',
										['null', 'null', max_events, type, 'null'])
				# if we are coming backward, we do not have request data. Hence isempty().
				db.commit()
				db.close()
			self.app.post('/bluesky_j_ctrl', data=dict({
				'mark-blocks':  mark_blocks
			}))
		# final
		with webscraping.app.app_context():
			db = webscraping.get_db()
			db.execute('SELECT max_events, type FROM args').fetchall() # there's only ever one row in this db.
			db.close()
		self.app.get('/bluesky_j_final', data=dict({'pronouns': 'yes'}))

	def test_r_goback(self, age: str | None='yes', pronouns: str | None='yes', limit: str | None ='5'):
		"""Begin at REST final, then go back and resubmit"""
		# gothru
		self.test_r_gothru(age='yes', pronouns='yes')
		# final
		with webscraping.app.app_context():
			db = webscraping.get_db()
			db.execute('SELECT max_events, type FROM args').fetchall() # there's only ever one row in this db.
			db.close()
		self.app.post('/bluesky_r_final', data=dict())
		# back (ctrl)
		with webscraping.app.app_context():
			db = webscraping.get_db()
			if webscraping.isempty():
				db.execute('INSERT INTO args (bluesky_length, querystring, max_events, type, mark_blocks) VALUES (?,?,?,?,?)',
									['5', 'null', 'null', 'null', 'null'])
			# if we are coming backward, we do not have request data. Hence isempty().
			db.commit()
			db.close()
		self.app.post('/bluesky_r_ctrl', data=dict({
			'age': age,
			'pronouns': pronouns,
			'limit': limit 
		}))
		# final
		with webscraping.app.app_context():
			db = webscraping.get_db()
			db.execute('SELECT max_events, type FROM args').fetchall() # there's only ever one row in this db.
			db.close()
		self.app.post('/bluesky_r_final', data=dict())

	def test_j_goback(self, max_events='5', type='post', querystring='a', mark_blocks: str | None='yes'):
		"""Begin at jetstream final, then go back and resubmit"""
		# gothru
		self.test_j_gothru(max_events=max_events, type=type)
	  # back (ctrl)
		if type == 'post':
			with webscraping.app.app_context():
				db = webscraping.get_db()
				if webscraping.isempty():
					db.execute('INSERT INTO args (bluesky_length, querystring, max_events, type, mark_blocks) VALUES (?,?,?,?,?)',
										['null', 'null', max_events, type, 'null'])
				# if we are coming backward, we do not have request data. Hence isempty().
				db.commit()
				db.close()
			self.app.post('/bluesky_j_ctrl', data=dict({
				'querystring': querystring 
			}))
		elif type == 'follow':
			with webscraping.app.app_context():
				db = webscraping.get_db()
				if webscraping.isempty():
					db.execute('INSERT INTO args (bluesky_length, querystring, max_events, type, mark_blocks) VALUES (?,?,?,?,?)',
										['null', 'null', max_events, type, 'null'])
				# if we are coming backward, we do not have request data. Hence isempty().
				db.commit()
				db.close()
			self.app.post('/bluesky_j_ctrl', data=dict({
				'mark-blocks': mark_blocks
			}))
		# final
		with webscraping.app.app_context():
			db = webscraping.get_db()
			db.execute('SELECT max_events, type FROM args').fetchall() # there's only ever one row in this db.
			db.close()
		self.app.post('/bluesky_j_final', data=dict())

	def test_r_tomain(self, age='yes', pronouns='yes', limit: str | None='5'):
		"""Begin at REST final, then go to main and resubmit"""
		# gothru
		self.test_r_gothru(age=age, pronouns=pronouns, limit=limit)
		# main
		self.app.post('/', data=dict())
		# gothru
		self.test_r_gothru(age=age, pronouns=pronouns, limit=limit)

	def test_j_tomain(self, max_events='5', type='post', querystring='a', mark_blocks: str | None='yes'):
		"""Begin at jetstream final, then go to main and resubmit"""
		if type == 'post':
			# gothru
			self.test_j_gothru(max_events=max_events, type=type, querystring=querystring)
			# main
			self.app.post('/', data=dict())
			# gothru
			self.test_j_gothru(max_events=max_events, type=type, querystring=querystring)
		elif type == 'follow':
			self.test_j_gothru(max_events=max_events, type=type, mark_blocks=mark_blocks)
			# main
			self.app.post('/', data=dict())
			# gothru
			self.test_j_gothru(max_events=max_events, type=type, mark_blocks=mark_blocks)

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
		with open(os.path.relpath('../csvfiles/bsky-jetstream.csv')) as file:
			while file.readline():
				text = file.readline()
				assert 'a' in text.split(',')[1]
		# columns
		self.test_j_gothru(type='follow', mark_blocks=None)
		with open(os.path.relpath('../csvfiles/bsky-jetstream.csv')) as file:
			text = file.readline()
			assert len(text.split(',')) == 3 
		self.test_j_gothru(type='follow', mark_blocks='yes')
		with open(os.path.relpath('../csvfiles/bsky-jetstream.csv')) as file:
			text = file.readline()
			assert len(text.split(',')) == 4 

	def test_r_time(self):
		"""Ensure that it doesn't take too long to create the csv."""
		start = perf_counter_ns()
		self.test_r_gothru(age=None, pronouns=None)	
		end = perf_counter_ns()
		duration = (end - start) / (10**9) # in seconds
		assert duration < 3 # takes less than three seconds to complete 5-row csv.

	def test_j_time(self):
		"""Ensure that it doesn't take too long to create the csv."""
		start = perf_counter_ns()
		self.test_j_gothru(type='post', querystring='a')
		end = perf_counter_ns()
		duration = (end - start) / (10**9) # in seconds
		assert duration < 1 # takes less than three seconds to complete 5-row csv.

if __name__ == "__main__":
	unittest.main()