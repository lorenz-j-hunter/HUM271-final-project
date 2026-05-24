import os, requests, asyncio  
from flask import Flask, render_template, g, request, redirect, url_for
from sqlite3 import dbapi2 as sqlite3
from utils.utils import get_age 
from logic import originals as responses
from logic import process
from logic import csv as files
from utils.classes import compound

"""Create the app and make db commands."""
app = Flask(__name__)

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


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('database/schema.sql', mode='r') as f:
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
  """Begin the jetstream for Bluesky."""
  responses.loop.call_soon_threadsafe(
    asyncio.create_task,
    responses.jetstream_worker(max_events=50)
  )
  return render_template('bluesky.html') 


@app.route('/', methods=['GET'])
def main():
  return render_template('main.html')


@app.route('/bluesky', methods=['POST', 'GET'])
def bluesky():
  """Open the route which uses the bluesky api.
  Here, we gather the info needed to create a CSV
  We store the following data as columns:
  - username
  - gender/pronouns
  - the user's follows (who they are following)
  - the user's posts (title text)
  """
  if request.method == 'GET':
    init_db()
    # Before we do anything, we need to reset.
    # This means getting API responses and deleting the previous 
    # request information.
    with get_db() as db:
      db.execute('DELETE FROM first_dim_for_bluesky')
      db.execute('DELETE FROM second_dim_for_bluesky')
      db.commit()
    bluesky_length: int = 10
    # Here, we bug-check. We ensure the user entered valid input.
    try:
      bluesky_length = int(request.args.get('bluesky_length', 'None')) 
    except ValueError:
      return redirect(url_for('static', filename='notfound.html'))
    process.bsky(db, bluesky_length) 
    files.get_bluesky_csv(db)      
    return render_template('bluesky.html')
  return render_template('bluesky.html')

@app.route('/x', methods=['GET', 'POST'])
def x():
  """Open the route which uses the x api. 
  - Here, we gather the info needed to create a CSV
  - We also store the data we fetch in a database.
  - The raw data is sent as arguments into an HTML file, while
    raw data is also stored in a database should a developer
    want to operate on it.
  """
  # We have dictionaries of (1) user responses, (2) follows responses, and (3) post responses from above.
  # Now, we (1) create item objects of them, (2) store them in lists, (3) put them in the database.
  # We also add to the second dimension if necessary.
  #
  # So we begin right here with creating item objects and storing those in lists. 
  if request.method == 'GET':
    init_db()
    x_length: int = 10 # The user is required to write to this.
    # Here, we bug-fix. We raise an error if the user entered the wrong data. 
    try:
      x_length = int(request.args.get('x_length', 'None')) 
    except ValueError:
      return redirect(url_for('static', filename='notfound.html'))
    db = get_db()
    process.x(db, x_length)
    files.get_x_csv(db)
    return render_template('x.html')
  return render_template('x.html')

@app.route('/pornhub', methods=['POST', 'GET'])
def pornhub():
  """Open the route which uses the pornhub api. 
  - Here, we gather the info needed to create a CSV
  - We also store the data we fetch in a database.
  - The raw data is sent as arguments into an HTML file, while
    raw data is also stored in a database should a developer
    want to operate on it.
  """
  if request.method == 'GET':
    init_db()
    pornhub_length: int = 10 # user is required to write to this
    # Here, we bug-fix. We raise an error if the user entered the wrong data.
    try:
      pornhub_length = int(request.args.get('pornhub_length', 'None')) 
    except ValueError:
      return redirect(url_for('static', filename='notfound.html'))
    db = get_db()
    process.pornhub(db, request, pornhub_length)
    files.get_pornhub_csv(db)
    return render_template('pornhub.html')
  return render_template('pornhub.html')
