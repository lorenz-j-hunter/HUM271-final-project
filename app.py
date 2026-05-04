import os, time, requests  # pyright: ignore[reportMissingModuleSource]
from utility.classes import item
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, render_template, g
from utility.utilities import get_auth, make_token


"""Global API responses for Bluesky."""
def get_bluesky() -> requests.Response:
  # We use 'actors' to get a query of said actor's feed. 
  b_actors_endpoint = "https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors"
  # All endpoint parameters used.
  bluesky_length: int = 5
  b_actors_params: dict[str, str | int] = {
    "q" : "a", # keep the query down to one vowel to maximize the search results. 
    "limit" : bluesky_length 
  }
  # The responses created with these endpoints and their parameters.
  actors: requests.Response = requests.get(
    b_actors_endpoint, b_actors_params
  )
  return actors


"""Global API responses for X."""
def get_x() -> list[list[str] | dict[str, str] | dict[str, list]]:
  # Just so you know, we only get these in order to get author ids. 
  x_posts_url = "https://api.x.com/2/tweets/search/all"

  x_posts_headers = {"Authorization": f"Bearer {get_auth('x_bearer_token.txt')}"}

  x_posts_params = {
    "query": "lang:en a e i o u",
    "start_time": "2020-01-01T00:00:00Z",
    "end_time": "2026-01-01T00:00:00Z",
    "max_results": 10,
    "tweet.fields": ['author_id'],
    "user.fields": ['username']
  }

  x_posts_response = requests.get(x_posts_url, headers=x_posts_headers, params=x_posts_params)
  print('\nBeginning the X posts response.\n\n', x_posts_response.json(), '\n\n')

  x_user_ids: list[str] = []
  for post in x_posts_response.json().get('data'):
    x_user_ids.append(post.get('author_id'))

  # Now, we map the user ids to the usernames that they bear. 
  # We need to do this before we call requests.

  x_users: dict[str, str] = {}
  for id in x_user_ids:

    url = f"https://api.x.com/2/users/{id}"

    headers = {"Authorization": f"Bearer {get_auth('x_bearer_token.txt')}"}

    params = {"user.fields": ['username']}

    response = requests.get(url, headers=headers, params=params)

    print('\n\nHere is a response from /2/users/id.\n', response.text, '\n\n')

    x_users[id] = response.json().get('data').get('username')

  # Now, we get follow data.
  x_follows: dict[str, list[str]] = {}
  for id in x_user_ids:
    # Make the request.
    url = f"https://api.x.com/2/users/{id}/following"

    headers = {"Authorization": f"Bearer {get_auth('x_bearer_token.txt')}"} 

    params = {"max_results": 10}

    response = requests.get(url, headers=headers, params=params)


    print('\nBeginning the X follows response.\n\n', response.text, '\n\n')
    # Map it to the user.
    json_list: list[dict[str, str]] = response.json().get('data')
    real_list: list[str] = []
    for element in json_list:
      real_list.append(element.get('id')) # type: ignore
    x_follows[id] = real_list

  # Now, we get a list of posts for each user.
  x_posts: dict[str, list[str]] = {}
  for id in x_user_ids:
    time.sleep(10) # rate limits.
    # Make the request.
    url = f"https://api.x.com/2/users/{id}/tweets"

    headers = {"Authorization": f"Bearer {get_auth('x_bearer_token.txt')}"}

    response = requests.get(url, headers=headers)

    print('Beginning the X posts response.\n\n', response.text, '\n\n')
    # Map it to the user.
    if response.json().get('data') is None:
      print("\n\nThe response for an index of x_posts was None. ")
    else:
      json_list: list[dict[str, str]] = response.json().get('data')
      real_list: list[str] = []
      for element in json_list:
        real_list.append(element.get('text')) # type: ignore
      x_posts[id] = real_list

  return [x_user_ids, x_users, x_follows, x_posts] 

  # In conclusion, we now have (1) a list of responses for users, (2) a list of responses for follows,
  # (3) a list of responses for posts. Those are x_user_ids, x_follows, and x_posts, respectively.
  # This all is for X. 

"""Global API responses for Pornhub."""
url = "https://pornhub2.p.rapidapi.com/v2/video_by_id"

pornhub_length = 100
pornhub_responses: list[requests.Response] = []
for i in range(pornhub_length):
  querystring = {"id":make_token(),"thumbsize":"small"}
  headers = {
    "x-rapidapi-key": get_auth('pornhub_key.txt'),
    "x-rapidapi-host": "pornhub2.p.rapidapi.com",
    "Content-Type": "application/json"
  }
  pornhub_responses.append(requests.get(url, headers=headers, params=querystring))
try:
  assert pornhub_responses[0].status_code == 200
except AssertionError:
  print(f"pornhub_responses[0].status_code == {pornhub_responses[0].status_code}") 


"""Create the app and make db commands."""
app = Flask(__name__)

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


# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database.db'),
    SECRET_KEY=get_auth('secret_key.txt'),
))
app.config.from_envvar('HUM271_SETTINGS', silent=True)

@app.route('/', methods=['GET'])
def main():
  return render_template('main.html')

@app.route('/bluesky', methods=['POST'])
def bluesky():
  """Open the route which uses the bluesky api. 
  - Here, we gather the info needed to create a CSV
  - We also store the data we fetch in a database.
  - The raw data is sent as arguments into an HTML file, while
    raw data is also stored in a database should a developer
    want to operate on it.
  """
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
  for actor in range(bluesky_limit): # type: ignore
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
      insertion_list: list[item] = []
      for i in range(posts_limit):
        # insert an item.
        insertion: item = item({
          'data' : post_response.json().get('posts')[i].get('uri'),
          'did' : identifier,
          'platform' : 'bluesky',
          'type' : 'posts'
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
      # Insert an item.
      insertion_list: list[item] = []
      for i in range(follows_limit):
        insertion: item = item({
          'data' : follows_response.json().get('follows')[i].get('did'),
          'did' : identifier,
          'platform' : 'bluesky',
          'type' : 'follows'
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
        'data' : actors.json().get('actors')[i].get('displayName'),
        'did' : actors.json().get('actors')[i].get('did'),
        'platform' : 'bluesky',
        'type' : 'user'
      }) 
      db.execute('INSERT INTO first_dim_for_bluesky (col_head_users) VALUES (?)', str(insertion))
      db.execute('INSERT INTO first_dim_for_bluesky (col_head_follows) VALUES (?)', 'head')
      db.execute('INSERT INTO first_dim_for_bluesky (col_head_posts) VALUES (?)', 'head')
      db.commit()
      # Now we add to the second dimension for follows. 
      insertion_list: list[item] = all_follows[identifiers[i]]
      for i in range(follows_limit):
        db.execute('INSERT INTO second_dim_for_bluesky (col_len_follows) VALUES (?)', str(insertion_list[i]))
        db.commit()
      # now we add to the second dimension for posts.
      insertion_list: list[item] = all_posts[identifiers[i]]
      for i in range(posts_limit):
        db.execute('INSERT INTO second_dim_for_bluesky (col_len_posts) VALUES (?)', str(insertion_list[i]))
        db.commit()     
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
  with get_db() as db:
    for user in x_user_ids:
      insertion: item = item({
        'data': x_users[user],
        'did': user,
        'platform': 'x',
        'type': 'users'
      })
      db.execute('INSERT INTO first_dim_for_x (col_head_users) VALUES (?)',
                [str(insertion)])
      db.commit()

      insertion: item = item({
        'data': 'head',
        'did': user,
        'platform': 'x',
        'type': 'follows'
      })
      # If this is the start of a two-dimensional data, then we enter 'head'.
      db.execute("INSERT INTO first_dim_for_x (col_head_follows) VALUES (?)", [str(insertion)])
      db.commit()
      print('\n\n', insertion, '\n\n') 

      insertion: item = item({
        'data': 'head',
        'did': user,
        'platform': 'x',
        'type': 'posts' 
      })
      db.execute("INSERT INTO first_dim_for_x (col_head_posts) VALUES (?)", [str(insertion)])
      db.commit()
      print('\n\n', insertion, '\n\n') 
    # Here we begin adding to the second dimension, starting with follows. 
    with get_db() as db:
      for user in x_user_ids:
        insertion: item = item({
          'data': x_follows[user],
          'did': user,
          'platform': 'x',
          'type': 'follows'
        })
        db.execute("INSERT INTO second_dim_for_x (col_len_follows) VALUES (?)", [str(insertion)])
        db.commit()
        print('\n\n', insertion, '\n\n') 
        insertion: item = item({
          'data': x_posts[user],
          'did': user,
          'platform': 'x',
          'type': 'posts'
        })
        db.execute("INSERT INTO second_dim_for_x (col_len_posts) VALUES (?)", [str(insertion)])
        db.commit()
        print('\n\n', insertion, '\n\n') 
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
  for i in range(pornhub_length):
    raw: list[dict[str, str]] = pornhub_responses[i].json().get('data').get('video').get('tags')
    string_list: list[str] = []
    for element in raw:
      string_list.append(element.get('tag_name')) # pyright: ignore[reportArgumentType]
      insertion: item = item({
        'data' : element.get('tag_name', 'none'),
        'did' : 'none',
        'platform' : 'pornhub',
        'type' : 'tags'
      })
      actual_tags.append(insertion)
    insertion: item = item({
      'data' : 'head',
      'did' : 'none',
      'platform' : 'pornhub',
      'type' : 'tags' 
    })
    tags.append(insertion)

    insertion: item = item({
      'data' : pornhub_responses[i].json().get('data').get('video').get('title'),
      'did' : 'none',
      'platform' : 'pornhub',
      'type' : 'title text'
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
      db.execute('INSERTO INTO second_dim_for_pornhub (col_len_tags) VALUES (?)',
                [str(actual_tags[i])])
  return render_template('pornhub.html')

