import os, asyncio
from flask import Flask, render_template, g, request, redirect, url_for, jsonify
from sqlite3 import dbapi2 as sqlite3
from logic import websocket as firehose 
from logic import insertion
from logic import csv as files
from logic import jetstream_csv as stream_files
from logic import backfill

"""Create the app and make db commands."""
app = Flask(__name__, static_folder='static')


# Load default config and override config from an environment variable
app.config.update(dict(
  DATABASE=os.path.join(app.root_path, 'database/database.db'),
  SECRET_KEY=os.environ['SECRET_KEY'],
))
app.config.from_envvar('HUM271_SETTINGS', silent=True)


def connect_db():
  """Connects to the specific database."""
  rv = sqlite3.connect(app.config['DATABASE'])
  rv.row_factory = sqlite3.Row
  return rv


def init_db(database='all'):
  """Initializes the database."""
  # check to see if arguments are valid.
  options: list[str] = ['all', 'bluesky', 'x', 'pornhub', 'jetstream', 'worker_done',
                        'list_of_stars', 'args']
  if database not in options:
    raise TypeError('init_db() argument not in list of options.')
  # Selectively initialize the database.
  db = get_db()
  if database == 'all':
    options.remove('all')
    for option in options:
      with app.open_resource(f'database/{option}.sql', mode='r') as f:
        db.cursor().executescript(f.read())
  else:
    with app.open_resource(f'database/{database}.sql', mode='r') as f:
      db.cursor().executescript(f.read())
  db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized all databases.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def isempty() -> bool:
  """Determine if table 'args' is empty"""
  db = get_db()
  f = db.execute('SELECT * FROM args').fetchall()
  if len(f) < 1:
    return True
  return False


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


"""Bluesky stream endpoints"""


@app.route('/bluesky_j_ctrl', methods=['GET', 'POST'])
def bluesky_j_ctrl():
  """Enter the page with which the user selects more options
  for jetstream control."""
  # The user will have entered some data we would like to save for later.
  db = get_db()
  if isempty():
    db.execute('INSERT INTO args (bluesky_length, querystring, max_events, type, mark_blocks) VALUES (?,?,?,?,?)',
              ['null', 'null', request.args.get('max_events'), request.args.get('pattern'), 'null'])
  # if we are coming backward, we do not have request data. Hence isempty().
  db.commit()
  db.close()
  return render_template('bluesky_j_ctrl.html')


@app.route('/start_jetstream_listener', methods=['GET'])
def start_jetstream_listener():
  """Enter the final page where the user downloads the csv.
  This activates the jetstream event listener."""
  # initialize the database
  init_db('jetstream')
  init_db('worker_done')
  print(f'request.args.get(\'mark-blocks\')={request.args.get('mark-blocks')}')
  print(f'request.args.get(\'querystring\')={request.args.get('querystring')}')
  # Extract the data user entered from page before.
  db = get_db()
  f = db.execute('SELECT max_events, type FROM args').fetchall() # there's only ever one row in this db.
  db.close()
  max_events = [row[0] for row in f][0]
  type = [row[1] for row in f][0]
  params = {
    'max_events': int(max_events),
    'event_type': type,
    'mark_blocks': None if request.args.get('mark_blocks') else request.args.get('mark_blocks'),
    'querystring': None if request.args.get('querystring') == '' else request.args.get('querystring')
  }
  # begin worker. 
  firehose.loop.call_soon_threadsafe(
    asyncio.create_task,
    firehose.jetstream_worker(
      db_path=app.config['DATABASE'],
      params=params
    )
  )
  return render_template('bluesky_j_final.html')


# Auxiliary funcs 


@app.route('/worker_status')
def worker_status():
  """Activate a feature only once the jetstream worker is done."""
  db = get_db()
  cur = None
  while cur is None:
    try:
      cur = db.execute('SELECT value FROM worker_done')
    except sqlite3.OperationalError:
      continue # keep trying until database not locked.
  f = cur.fetchall()
  worker_done = [row[0] for row in f][0]
  db.close()
  return jsonify({"done": worker_done})


@app.route('/bluesky_j_final/update_stream_db', methods=['POST'])
def update_stream_db():
  """Update the db to reflect changes."""
  init_db('worker_done')
  # update the graph without re-initialization.
  firehose.loop.call_soon_threadsafe(
    asyncio.create_task,
    firehose.jetstream_update(
      db_path=app.config['DATABASE'],
    )
  )
  return render_template('bluesky_j_final.html')

# End auxiliary funcs

"""End stream endpoints"""


@app.route('/', methods=['GET'])
def main():
  init_db()
  return render_template('main.html')


"""Bluesky REST Paths."""


@app.route('/bluesky', methods=['POST'])
def bluesky():
  """Open the first page of control for bluesky gathering. 
  This is the branching point at which the user chooses between
  jetstream and REST."""
  # clear store
  init_db('args')
  return render_template('bluesky.html')


@app.route('/bluesky_r_ctrl', methods=['POST', 'GET'])
def bluesky_r_ctrl():
  """Page in which, after completing request info, 
  user selects more options"""
  # Store the request info for use later.
  db = get_db()
  if isempty():
    db.execute('INSERT INTO args (bluesky_length, querystring, max_events, type, mark_blocks) VALUES (?,?,?,?,?)',
              [request.form['bluesky_length'], 'null', 'null', 'null', 'null'])
  # if we are coming backward, we don't have request.form['bluesky_length'].
  db.commit()
  db.close()
  return render_template('bluesky_r_ctrl.html')


@app.route('/get_rest_requests', methods=['GET', 'POST'])
def get_rest_requests():
  """Load the final page from which the user downloads their finished
  csv. This activates the REST request maker.
  """
  init_db('bluesky')
  init_db('worker_done')
  # get the value user entered before
  db = get_db()
  f = db.execute('SELECT bluesky_length FROM args').fetchall()
  bluesky_length = [row[0] for row in f][0]
  db.close()
  # get params
  params = {
    'bluesky_length': int(bluesky_length),
    'querystring': None if request.args.get('querystring') == '' else request.args.get('querystring'),
    'limit': None if request.args.get('limit') == '' else request.args.get('limit'),
    'columns': {
      'did': None if request.args.get('did') == '' else request.args.get('did'),
      'age': None if request.args.get('age') == '' else request.args.get('age'),
      'pronouns': None if request.args.get('pronouns') == '' else request.args.get('pronouns')
    }
  }
  print(f'params[\'columns\'].get(\'did\')={params['columns'].get('did')}')
  print(f'params[\'columns\'].get(\'age\')={params['columns'].get('age')}')
  print(f'params[\'columns\'].get(\'pronouns\')={params['columns'].get('pronouns')}')
  # clear the bluesky rest database.
  insertion.clear_bsky(app.config['DATABASE'])
  firehose.loop.call_soon_threadsafe(
    asyncio.create_task,
    insertion.bsky(
      db_path=app.config['DATABASE'],
      params=params
    )
  )
  return render_template('bluesky_r_final.html')


"""End Bluesky REST Paths."""


"""Begin X Paths."""


@app.route('/x', methods=['GET', 'POST'])
def x():
  """Open the route which uses the x api. 
  - Here, we gather the info needed to create a CSV
  - We also store the data we fetch in a database.
  """
  if request.method == 'GET':
    init_db('x')
    x_length: int = 10 # The user is required to write to this.
    # Here, we bug-fix. We raise an error if the user entered the wrong data. 
    try:
      x_length = int(request.args.get('x_length', 'None')) 
    except ValueError:
      return redirect(url_for('static', filename='notfound.html'))
    db = get_db()
    insertion.x(db, x_length)
    files.get_x_csv(db)
    return render_template('x.html')
  return render_template('x.html')


"""End X Paths."""


"""Begin Pornhub Paths."""


@app.route('/pornhub', methods=['POST', 'GET'])
def pornhub():
  """Open the route which uses the pornhub api. 
  - Here, we gather the info needed to create a CSV
  - We also store the data we fetch in a database.
  """
  if request.method == 'GET':
    init_db('pornhub')
    pornhub_length: int = 10 # user is required to write to this
    # Here, we bug-fix. We raise an error if the user entered the wrong data.
    try:
      pornhub_length = int(request.args.get('pornhub_length', 'None')) 
    except ValueError:
      return redirect(url_for('static', filename='notfound.html'))
    db = get_db()
    field_error = insertion.pornhub(db, request, pornhub_length)
    # if there is an error, just redirect control back 
    if field_error:
      return render_template('pornhub.html', code=True) 
    files.get_pornhub_csv(db)
    return render_template('pornhub.html')
  return render_template('pornhub.html')


"""End Pornhub Paths."""


@app.route('/docs', methods=['POST'])
def docs():
  """Manifesto and user manual."""
  return render_template('docs.html')

@app.route('/see_more', methods=['GET'])
def see_more():
  """What the user sees when they click 'see more'."""
  return render_template('see_more.html')

