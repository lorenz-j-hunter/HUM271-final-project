import os, time, requests  # pyright: ignore[reportMissingModuleSource]
from utility.classes import item
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, render_template, g, request
from api.responses import get_bluesky, get_x, get_pornhub
from utility.utilities import get_auth, encase

"""Create the app and make db commands."""
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database/database.db'),
    SECRET_KEY=get_auth('secret_key.txt'),
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

"""Create utility functions."""

def bluesky_follows_to_undirected_graph(all_follows: dict[str, list[str]], all_posts: dict[str, list[str]]):
  """Convert the database file (follows) into a csv.
  The csv represents an undirected and simple graph. Edge weight is 2."""
  with get_db() as db:
    # Here we get a list of the user ids.
    cur = db.execute('SELECT id, col_head_users FROM first_dim_for_bluesky')
    results: list[str] = cur.fetchall()
    users: list[str] = [row[1] for row in results]
    # Now, we get the follows of each user as a list. 
    for user in users:
      cur = db.execute('SELECT')
      pass


@app.route('/', methods=['GET'])
def main():
  return render_template('main.html')

@app.route('/bluesky', methods=['POST', 'GET'])
def bluesky():
  """Open the route which uses the bluesky api. 
  - Here, we gather the info needed to create a CSV
  - We also store the data we fetch in a database.
  - The raw data is sent as arguments into an HTML file, while
    raw data is also stored in a database should a developer
    want to operate on it.
  """
  if request.method == 'GET':
    package = get_bluesky()
    bluesky_length: int = package[0] # type: ignore
    actors: requests.Response = package[1] # type: ignore
    # This (identifiers) is a list of handles of users.
    # On same dimension as 'bluesky_length' but not for 'follows_limit'.
    identifiers: list[str] = []
    posts_endpoint: str = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
    follows_endpoint: str = "https://api.bsky.app/xrpc/app.bsky.graph.getFollows"
    # Key: Handle of user in question
    # Value: URI of text from post.
    all_posts: dict[str, list[item]] = {} 
    # Key: Handle of the user in question
    # Value: List of handles of follows.  
    all_follows: dict[str, list[item]] = {}
    follows_limit: int = 100
    posts_limit: int = 100
    for actor in range(bluesky_length): # type: ignore
      # Here, we traverse the thing by actor.
      # We separate actors' at-identifiers (did) from the json first. 
      for actor in actors.json().get('actors'):
        identifiers.append(actor.get('handle'))
      # Here, we gather all post data. 
      # It is stored in a dict; the DID of the user in question is
      # the key and the corresponding *list* of posts is the value.
      for identifier in identifiers:
        posts_params: dict[str, str | int] = {
          "q" : "a",
          "author" : identifier,
          'limit' : posts_limit 
        }
        post_response: requests.Response = requests.get(
          posts_endpoint, posts_params 
        )
        if post_response.status_code == 403: # AppView deliberately returns 403 to reduce load 
          continue 
        posts_limit = len(post_response.json().get('posts'))
        insertion_list: list[item] = []
        for i in range(posts_limit):
          # insert an item.
          insertion: item = item({
            'data' : encase('"', post_response.json().get('posts')[i].get('uri')),
            'did' : encase('"', identifier),
            'platform' : '"bluesky"',
            'type' : '"posts"',
            'item_id': encase('"', str(i))
          })
          insertion_list.append(insertion)
        all_posts[identifier] = insertion_list
        # Now here we gather all follow data.
        # These are inserted into a dictionary called 'all_follows', which
        # has as it's key the handle and as a value the list of all follows
        # (their handles).
        follows_params: dict[str, str | int] = {
          "actor" : identifier,
          "limit" : follows_limit 
        } 
        follows_response: requests.Response = requests.get(
          follows_endpoint, follows_params  
        )
        follows_limit = len(follows_response.json().get('follows'))
        # Insert an item.
        insertion_list: list[item] = []
        for i in range(follows_limit):
          insertion: item = item({
            'data' : encase('"', follows_response.json().get('follows')[i].get('did')),
            'did' : encase('"', identifier),
            'platform' : '"bluesky"',
            'type' : '"follows"',
            'item_id': encase('"', str(i))
          })
          insertion_list.append(insertion)
        all_follows[identifier] = insertion_list 
    # Finally, we add these columns to a database.
    # It's in the database that the data will be operated on
    # to find refined things like 'perceived opinion'.
    with get_db() as db:
      # We first insert to the first dimension here, then move onto the second dimension.
      for i in range(bluesky_length): # assume all of these lists are the same length
        insertion: item = item({
          'data' : encase('"', actors.json().get('actors')[i].get('displayName')),
          'did' : encase('"', actors.json().get('actors')[i].get('did')),
          'platform' : '"bluesky"',
          'type' : '"user"',
          'item_id': encase('"', str(i))
        }) 
        db.execute('INSERT INTO first_dim_for_bluesky (col_head_users, col_head_genders, col_head_follows, col_head_posts) VALUES (?, ?, ?, ?)',
                  [str(insertion), 'head', 'head', 'head'])
        db.commit()
        # Now we add to the second dimension for follows and posts. 
        for i in range(follows_limit):
          f_insertion_list: list[item] = all_follows[identifiers[i]]
          p_insertion_list: list[item] = all_follows[identifiers[i]]
          for e in range(min(len(f_insertion_list), len(p_insertion_list))):
            db.execute('INSERT INTO second_dim_for_bluesky (col_len_follows, col_len_posts) VALUES (?, ?)',
                      [str(f_insertion_list[e]), str(p_insertion_list[e])])
            db.commit()
    return render_template('bluesky.html', identifiers=identifiers)
  return render_template('bluesky.html')

@app.route('/x', methods=['POST'])
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
    package: list = get_x()
    x_user_ids: list[str] = package[0] # type: ignore
    x_users: dict[str, str] = package[1] # type: ignore
    x_follows: dict[str, list] = package[2] # type: ignore
    x_posts: dict[str, list] = package[3]
    with get_db() as db:
      for user in x_user_ids:
        user_insertion: item = item({
          'data': encase('"', x_users[user]), 
          'did': encase('"', user),
          'platform': '"x"',
          'type': '"users"',
          'item_id': '"none"'
        })
        follows_insertion: item = item({
          'data': '"head"',
          'did': encase('"', user),
          'platform': '"x"',
          'type': '"follows"',
          'item_id': '"none"'
        })
        posts_insertion: item = item({
          'data': '"head"',
          'did': encase('"', user),
          'platform': '"x"',
          'type': '"posts"',
          'item_id': '"none"'
        })
        # Two-dimensional data fields have 'head' as their entry in the first dimension.
        db.execute('INSERT INTO first_dim_for_x (col_head_users, col_head_follows, col_head_posts) VALUES (?, ?, ?)',
                  [str(user_insertion), str(follows_insertion), str(posts_insertion)])
        db.commit()
      # Here we begin adding to the second dimension, starting with follows. 
      with get_db() as db:
        for user in x_user_ids:
          follows_list = x_follows[user]
          posts_list = x_posts[user]
          for i in range(max([len(follows_list), len(posts_list)])):
            follows_insertion: item = item({
              'data': encase('"', str(follows_list[i])), # if it is None, it will be put in like that
              'did': encase('"', user),
              'platform': '"x"',
              'type': '"follows"',
              'item_id': '"none"'
            })
            posts_insertion: item = item({
              'data': encase('"', str(posts_list[i])),
              'did': encase('"', user),
              'platform': '"x"',
              'type': '"posts"',
              'item_id': '"none"'
            })
            db.execute("INSERT INTO second_dim_for_x (col_len_follows, col_len_posts) VALUES (?, ?)",
                        [str(follows_insertion), str(posts_insertion)])
            db.commit()
    return render_template('x.html', identifiers=x_user_ids)
  return render_template('x.html')

@app.route('/pornhub', methods=['POST'])
def pornhub():
  """Open the route which uses the pornhub api. 
  - Here, we gather the info needed to create a CSV
  - We also store the data we fetch in a database.
  - The raw data is sent as arguments into an HTML file, while
    raw data is also stored in a database should a developer
    want to operate on it.
  """
  if request.method == 'GET':
    package = get_pornhub()
    pornhub_length: int = package[0] # type: ignore
    pornhub_responses: list[requests.Response] = package[1] # type: ignore
    # These are our return values. Each represent a column of the CSV we want to create with this
    # function.
    # Pornhub doesn't have a rich text circulation, so we grab the title and tag.
    # We can assume that the demographic of watcher influences which type of video they
    # watch.
    # With that, we can compare data like title interpretations for 'perceived opinion',
    # quantity of one video group with quantity of another video group. 
    tags: list[item] = []
    actual_tags: list[item] = []
    title_text: list[item] = []
    # Traverse all of the fetched videos. Get their tags and titles, then
    # put those in 'item' objects. 
    for i in range(pornhub_length):
      time.sleep(5) # the api will send HTTP 429 - 'requests are coming too fast.'
      raw: list[dict[str, str]] = pornhub_responses[i].json().get('data').get('video').get('tags')
      string_list: list[str] = []
      for element in raw:
        string_list.append(element.get('tag_name')) # pyright: ignore[reportArgumentType]
        insertion: item = item({
          'data' : encase('"', element.get('tag_name', 'None')),
          'did' : '"None"',
          'platform' : '"pornhub"',
          'type' : '"tags"',
          'item_id': '"none"'
        })
        actual_tags.append(insertion)
      insertion: item = item({
        'data' : '"head"',
        'did' : '"None"',
        'platform' : '"pornhub"',
        'type' : '"tags"',
        'item_id': '"none"'
      })
      tags.append(insertion)

      insertion: item = item({
        'data' : encase('"', pornhub_responses[i].json().get('data').get('video').get('title')),
        'did' : '"None"',
        'platform' : '"pornhub"',
        'type' : '"title text"',
        'item_id': '"none"'
      })
      title_text.append(insertion)
    # Finally, we add these to the database.
    # We open the tables for both dimensions, as 'tags' has a second dimension.
    with get_db() as db:
      for i in range(pornhub_length):
        db.execute('INSERT INTO first_dim_for_pornhub (col_head_tags) VALUES (?)',
                  [str(tags[i])])
        db.execute('INSERT INTO first_dim_for_pornhub (col_head_title_text) VALUES (?)',
                  [str(title_text[i])])
        db.commit()
      for i in range(len(actual_tags)):
        db.execute('INSERT INTO second_dim_for_pornhub (col_len_tags) VALUES (?)',
                  [str(actual_tags[i])])
    return render_template('pornhub.html', identifiers='identifiers')
  return render_template('pornhub.html')

