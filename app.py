import os, asyncio
from flask import Flask, render_template, g, request, redirect, url_for, jsonify
from sqlite3 import dbapi2 as sqlite3
from logic import websocket as firehose 
from logic import db_insert
from logic import csv as files
from logic import jetstream_csv as stream_files

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
                        'list_of_stars']
  if database not in options:
    raise TypeError('init_db() argument not in list of options.')
  # Selectively initialize the database.
  db = get_db()
  if database == 'all':
    with app.open_resource('database/bluesky.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    with app.open_resource('database/x.sql', mode='r') as f:
      db.cursor().executescript(f.read()) 
    with app.open_resource('database/pornhub.sql', mode='r') as f:
      db.cursor().executescript(f.read()) 
  elif database == 'bluesky':
    with app.open_resource('database/bluesky.sql', mode='r') as f:
      db.cursor().executescript(f.read())
  elif database == 'x':
    with app.open_resource('database/x.sql', mode='r') as f:
      db.cursor().executescript(f.read()) 
  elif database == 'pornhub':
    with app.open_resource('database/pornhub.sql', mode='r') as f:
      db.cursor().executescript(f.read()) 
  elif database == 'jetstream':
    with app.open_resource('database/jetstream.sql', mode='r') as f:
      db.cursor().executescript(f.read()) 
  elif database == 'worker_done':
    with app.open_resource('database/worker_done.sql', mode='r') as f:
      db.cursor().executescript(f.read()) 
  elif database == 'list_of_stars':
    with app.open_resource('database/list_of_stars.sql', mode='r') as f:
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


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


"""Begin endpoints for html pages"""

@app.route('/start_jetstream_listener', methods=['GET'])
def start_jetstream_listener():
  """Begin the jetstream for Bluesky. Then create the CSV for it. """
  # initialize the database
  init_db('jetstream')
  init_db('worker_done')
  # begin worker. 
  firehose.loop.call_soon_threadsafe(
    asyncio.create_task,
    firehose.jetstream_worker(
      db_path=app.config['DATABASE'],
      max_events=int(request.args.get('max_events', '0')),
      event_type=request.args.get('pattern', 'post')
    )
  )
  return render_template('bluesky_1.html')


@app.route('/worker_status')
def worker_status():
  """Activate a feature only once the jetstream worker is done."""
  db = get_db()
  cur = db.execute('SELECT value FROM worker_done')
  f = cur.fetchall()
  worker_done = [row[0] for row in f][0]
  db.close()
  return jsonify({"done": worker_done})


@app.route('/get_stream_csv', methods=['GET'])
def get_stream_csv():
  """Get the csv while in bluesky_1."""
  stream_files.get_jetstream_csv(db_path=app.config['DATABASE'])
  return render_template('bluesky_1.html')



@app.route('/', methods=['GET'])
def main():
  init_db()
  init_db('worker_done')
  return render_template('main.html')

"""Bluesky Paths."""

@app.route('/bluesky', methods=['POST', 'GET'])
def bluesky():
  """Open the route which uses the bluesky api.
  - Here, we gather the info needed to create a CSV
  - We also store the stuff in a SQLite database
  """
  if request.method == 'GET':
    init_db('bluesky')
    # Before we do anything, we need to reset.
    # This means getting API responses and deleting the previous 
    # request information.
    with get_db() as db:
      db.execute('DELETE FROM first_dim_for_bluesky')
      db.execute('DELETE FROM second_dim_for_bluesky')
      db.commit()
    bluesky_length: int = 10
    db_insert.bsky(db, bluesky_length) 
    return render_template('bluesky.html')
  return render_template('bluesky.html')

@app.route('/bluesky_1', methods=['POST'])
def bluesky_1():
  """Page in which, after a complete request, CSV download
  is an option."""
  db = get_db()
  files.get_bluesky_csv(db)
  return render_template('bluesky_1.html')

"""End Bluesky Paths."""


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
    db_insert.x(db, x_length)
    files.get_x_csv(db)
    return render_template('x.html')
  return render_template('x.html')

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
    field_error = db_insert.pornhub(db, request, pornhub_length)
    # if there is an error, just redirect control back 
    if field_error:
      return render_template('pornhub.html', code=True) 
    files.get_pornhub_csv(db)
    return render_template('pornhub.html')
  return render_template('pornhub.html')

@app.route('/docs', methods=['POST'])
def docs():
  """Manifesto and user manual."""
  return render_template('docs.html')

@app.route('/see_more', methods=['GET'])
def see_more():
  """What the user sees when they click 'see more'."""
  return render_template('see_more.html')

