from flask import Flask, render_template, request, g
import requests # pyright: ignore[reportMissingModuleSource]
from typing import Any
import os
from sqlite3 import dbapi2 as sqlite3

"""Global API endpoints."""
# We use 'actors' to get a query of said actor's feed. 
actors_endpoint = "https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors"

# All endpoint parameters used.
actors_params: dict[str, str | int] = {
  "q" : "a", # keep the query down to one vowel to maximize the search results. 
  "limit" : 5 
}

# The responses created with these endpoints and their parameters.
actors: requests.Response = requests.get(
  actors_endpoint, actors_params
)

app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database.db'),
    SECRET_KEY='development key',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


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

@app.route('/', methods=['GET','POST'])
def bluesky():
  """Open the main route for the app.
  Here, we gather the info needed to create a CSV
  """
  # These are our return values. Each represent a column of the CSV we want to create with this
  # function.
  # We also include 'identifiers'. This is the DID of users in question. It is used later.
  users: list[str] = []
  genders: list[str] = []
  follows: list[str] = []
  text: list[str] = []
  # This is a list of handles of users. 
  identifiers: list[str] = []
  # Now that we have a list of actors from global, we can search their feeds locally.
  posts_endpoint: str = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
  follows_endpoint: str = "https://api.bsky.app/xrpc/app.bsky.graph.getFollows"
  # Key: Handle of user in question
  # Value: URI of text from post.
  all_posts: dict[str, str] = {} 
  # Key: Handle of the user in question
  # Value: Handle of the followed user 
  all_follows: dict[str, str] = {}
  for actor in range(actors_params.get('limit')): # type: ignore
    # Here, we traverse the thing by actor.
    # We separate actors' at-identifiers (did) from the json first. 
    for actor in actors.json().get('actors'):
      identifiers.append(actor.get('handle'))
    # Here, we gather all post data. 
    # It is stored in a dict; the DID of the user in question is
    # the key and the corresponding *list* of posts is the value.
    # We limit the number of posts to 5.
    for identifier in identifiers:
      posts_params: dict[str, str | int] = {
        "q" : "a",
        "author" : identifier,
        'limit' : 1 
      }
      post_response: requests.Response = requests.get(
        posts_endpoint, posts_params 
      )
      all_posts[identifier] = post_response.json().get('posts')[0].get('uri')
      # Now here we gather all follow data.
      # These are inserted into a dictionary called 'all_follows', which
      # has as it's key the handle and as a value the list of all follows
      # (their handles).
      # We limit the number of follows to 1.
      follows_params: dict[str, str | int] = {
        "actor" : identifier,
        "limit" : 1 
      } 
      follows_response: requests.Response = requests.get(
         follows_endpoint, follows_params  
      )
      all_follows[identifier] = follows_response.json().get('follows')[0].get('handle')
  # Now we extract from the dict of posts we just got. 
  # We gather all of the columns for the CSV at this point.
  # Those four columns were (1) actor, (2) gender, (2) perceived audience, (3) Perceived opinion.
  # We create four variables now, each of which represents a column

  for i in range(actors_params.get('limit')): # type: ignore
    # the 'displayName' key is not required. 
    if (actors.json().get('actors')[i].get("displayName") is not None):
      users.append(actors.json().get('actors')[i].get('displayName'))
    else:
      users.append('none') 
    # The 'pronouns' key is not required.
    if (actors.json().get('actors')[i].get('pronouns') is not None):
      genders.append(actors.json().get('actors')[i].get('pronouns'))
    else:
      genders.append('none')
  for identifier in identifiers:
    follows.append(all_follows[identifier])
    text.append(all_posts[identifier])
  # Finally, we add these columns to a database.
  # It's in the database that the data will be operated on
  # to find refined things like 'perceived opinion'.
  db = get_db()
  for row in range(len(users)):
    db.execute("INSERT INTO bluesky (user, gender, follows, text) VALUES (?, ?, ?, ?)",
              [users[row], genders[row], follows[row], text[row]])
    db.commit()
  return render_template('main.html', users=users, genders=genders, follows=follows, text=text)