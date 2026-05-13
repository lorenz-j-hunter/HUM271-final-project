import os, time, requests  # pyright: ignore[reportMissingModuleSource]
from utility.classes import item
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, render_template, g, request
from utility.utilities import get_auth, encase, extract

def get_bluesky(bluesky_length: int) -> dict[str, list[dict[str, str]]]:
  """API responses from Bluesky.
  `JSON` bodies are collected, then condensed into a dict.
  Return actors, where `actors` is the schema of the
  collection of bluesky responses.

  *Arguments* 
  bluesky_length (int) : the number of actors to query for.
  
  *Return value*
  actors (dict[str, list[dict[str,str]]]) : A dict that resembles the schema from docs.bsky.com
  for this endpoint."""
  # This is a 'searchActors' query only.
  endpoint = "https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors"
  # We paginate through the search list until the `actors` is filled. 
  cursor = None 
  actors_list: list[requests.Response] = []
  while len(actors_list) <= bluesky_length:
    params: dict[str, str | int] = {
      "q" : 'lang:en a e i o u',
      "limit" : 1 
    }
    if cursor:
      params["cursor"] = cursor
    # This is the response created with this endpoint and their parameters.
    response = requests.get(endpoint, params)
    cursor = response.json().get('cursor')
    actors_list.append(response)
  # Here, we compress the list of responses into a single response. 
  actors: dict[str, list[dict[str, str]]] = {
    'actors': []
  } 
  # Finally, we return the schema.
  # This is the schema that can be found on docs.bsky.com for this endpoint.
  # However, we only return one element of the schema: 'actors'.
  # That's like returning only one pair of a normal `requests.Response`. 
  for actor in actors_list:
    if len(actor.json().get('actors')) > 0: # Some pages do not have any actors on them ... ? 
      actors['actors'].append(actor.json().get('actors')[0]) 
  return actors

"""Global API responses for X."""
def get_x(x_length: int) -> list[list[str] | dict[str, str] | dict[str, list]]:
  """API responses from X.
  Return [x_user_ids, x_users, x_follows, x_posts], where `x_user_ids` is `list[str],
  `x_users` is `dict[str, str]`, `x_follows` is `dict[str, list[str]]`, and
  `x_posts` is `dict[str, list[str]]`."""
  # Just so you know, we only get these in order to get author ids. 
  x_posts_url = "https://api.x.com/2/tweets/search/all"
  x_posts_headers = {"Authorization": f"Bearer {get_auth('x_bearer_token.txt')}"}
  x_posts_params = {
    "query": "lang:en a e i o u",
    "start_time": "2020-01-01T00:00:00Z",
    "end_time": "2026-01-01T00:00:00Z",
    "max_results": x_length,
    "tweet.fields": ['author_id'],
    "user.fields": ['username']
  }
  x_posts_response = requests.get(x_posts_url, headers=x_posts_headers, params=x_posts_params)
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
    x_users[id] = response.json().get('data').get('username')

  # Now, we get follow data.
  x_follows: dict[str, list[str]] = {}
  for id in x_user_ids:
    # Make the request.
    url = f"https://api.x.com/2/users/{id}/following"
    headers = {"Authorization": f"Bearer {get_auth('x_bearer_token.txt')}"} 
    params = {"max_results": 10}
    response = requests.get(url, headers=headers, params=params)
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
    # Map it to the user.
    if response.json().get('data') is None:
      continue
    else:
      json_list: list[dict[str, str]] = response.json().get('data')
      real_list: list[str] = []
      for element in json_list:
        real_list.append(element.get('text')) # type: ignore
      x_posts[id] = real_list

  return [x_user_ids, x_users, x_follows, x_posts] 


def get_pornhub(pornhub_length: int) -> list[list[requests.Response] | list[str]]:
  """API responses for Pornhub. 
  Return [pornhub_length, video_search, pornstars], where `pornhub_length` is the number of videos
  that were requested, `video_search` is `list[requests.Response]`, and `pornstars` is
  `list[requests.Response]`."""

  video_search: list[requests.Response] = []
  # Here, we only search for pornstars. 
  url = "https://pornhub2.p.rapidapi.com/v2/stars_detailed"

  querystring = {"offset":"0","limit":str(pornhub_length)}
  headers = {
    "x-rapidapi-key": get_auth('pornhub_key.txt'),
    "x-rapidapi-host": "pornhub2.p.rapidapi.com",
    "Content-Type": "application/json"
  }
  # Here, we process the request. We make it into a list of strings. 
  stars_response: list[dict[str,str]] = requests.get(url, headers=headers, params=querystring).json().get('stars')
  pornstars: list[str] = []
  for star in stars_response:
    pornstars.append(star['star_name']) 
  # Now, we fetch a list of videos associated with these stars. 
  for _ in range(pornhub_length):
    url = "https://pornhub2.p.rapidapi.com/v2/search"
    querystring = {"search":"oiled",
                  "page":"1",
                  "period":"weekly",
                  "stars":pornstars,
                  "ordering":"newest",
                  "thumbsize":"small"}
    headers = {
      "x-rapidapi-key": get_auth('pornhub_key.txt'),
      "x-rapidapi-host": "pornhub2.p.rapidapi.com",
      "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers, params=querystring)
    video_search.append(response)
  # Finally, we are ready to return.
  return [video_search, pornstars]


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
    init_db()
    # Before we do anything, we need to reset.
    # This means getting API responses and deleting the previous 
    # request information.
    with get_db() as db:
      db.execute('DELETE FROM first_dim_for_bluesky')
      db.execute('DELETE FROM second_dim_for_bluesky')
      db.commit()
    bluesky_length = 15 # this is arbitrary
    actors: dict[str, list[dict[str, str]]] = get_bluesky(bluesky_length) 
    # Now we define some common variables. 
    # `identifiers` is a list of handles of users.
    # This is on same dimension as 'bluesky_length' but not for 'follows_limit'.
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
    # Here, we traverse the thing by actor.
    # We separate actors' handles from the json first to do this.
    for e in actors['actors']:
      identifiers.append(e['handle'])
    for identifier in identifiers:
      # Here, we gather all post data of the user in question.
      # It is stored in a dict; the DID of the user in question is
      # the key and the corresponding *list* of posts is the value.
      posts_params: dict[str, str | int] = {
        "q" : "a",
        "author" : identifier,
        'limit' : posts_limit 
      }
      post_response: requests.Response = requests.get(
        posts_endpoint, posts_params 
      )
      if post_response.status_code == 403: # AppView deliberately returns 403 to reduce load 
        all_posts[identifier] = []
        all_follows[identifier] = []
        continue 
      posts_limit = len(post_response.json().get('posts'))
      insertion_list: list[item] = []
      for i in range(posts_limit):
        # insert an item.
        insertion: item = item({
          'data' : encase('"', f'data:{post_response.json().get('posts')[i].get('uri')}'),
          'did' : encase('"', f'did:{identifier}'),
          'platform' : '"platform:bluesky"',
          'type' : '"type:posts"',
          'item_id': encase('"', f'item_id:{str(i)}')
        })
        insertion_list.append(insertion)
      all_posts[identifier] = insertion_list
      # Now here we gather all follow data of the user in question.
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
      if follows_response: # Sometimes, follows_response is None. 
        follows_limit = len(follows_response.json().get('follows'))
        # Insert an item.
        insertion_list: list[item] = []
        for i in range(follows_limit):
          insertion: item = item({
            'data' : encase('"', f'data:{follows_response.json().get('follows')[i].get('did')}'),
            'did' : encase('"', f'identifier:{identifier}'),
            'platform' : '"platform:bluesky"',
            'type' : '"type:follows"',
            'item_id': encase('"', f'item_id:{str(i)}')
          })
          insertion_list.append(insertion)
        all_follows[identifier] = insertion_list 
      else: # In this case, we still have to fill all_follows with something.
        insertion_list: list[item] = []
        all_follows[identifier] = insertion_list
    # Finally, we add these columns to a database.
    # It's in the database that the data will be operated on
    # to find refined things like 'perceived opinion'.
    with get_db() as db:
      # We first insert to the first dimension here, then move onto the second dimension.
      for actor in range(bluesky_length): # assume all of these lists are the same length
        insertion: item = item({
          'data' : encase('"', f'data:{actors['actors'][actor].get('displayName', 'None')}'), 
          'did' : encase('"', f'did:{actors['actors'][actor].get('did', 'None')}'),
          'platform' : '"platform:bluesky"',
          'type' : '"type:user"',
          'item_id': encase('"', f'item_id:{str(actor)}')
        }) 
        db.execute('INSERT INTO first_dim_for_bluesky (col_head_users, col_head_genders, col_head_follows, col_head_posts) VALUES (?, ?, ?, ?)',
                  [str(insertion), 'head', 'head', 'head'])
        db.commit()
        # Now we add to the second dimension for follows and posts. 
        # First we insert into both columns for follows. Then, we update the rows
        # that have been filled with posts.
        # Finally, to cover all cases, we may insert after that, too.
        for _ in range(follows_limit):
          f_insertion_list: list[item] = all_follows[identifiers[actor]]
          for e in range(len(f_insertion_list)):
            db.execute('INSERT INTO second_dim_for_bluesky (col_len_follows, col_len_posts) VALUES (?, ?)',
                      [str(f_insertion_list[e]), 'None'])
            db.commit()
        for _ in range(posts_limit):
          f_insertion_list_len: int = len(all_follows[identifiers[actor]])
          p_insertion_list: list[item] = all_posts[identifiers[actor]]
          # We first update what has already been inserted.
          for e in range(f_insertion_list_len):
            db.execute('UPDATE second_dim_for_bluesky SET col_len_posts = (?) WHERE id == (?)',
                        [str(p_insertion_list[e]), e])
            db.commit()
          # Then, we continue to insert if there are more posts than follows. 
          if len(p_insertion_list) > f_insertion_list_len:
            for e in range(f_insertion_list_len, len(p_insertion_list)):
              db.execute('INSERT INTO second_dim_for_bluesky (col_len_follows, col_len_posts) VALUES (?, ?)',
                          ['None', str(p_insertion_list[e])])
              db.commit()
      # We will pull data from another function in order to display the results.
      # If we do want to send anything in as an argument, it will be something
      # that is required for this. 
      return render_template('bluesky.html', identifiers=identifiers)
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
    package: list = get_x(10) # return, at most, 10 responses.
    x_user_ids: list[str] = package[0] 
    x_users: dict[str, str] = package[1] 
    x_follows: dict[str, list[str]] = package[2] 
    x_posts: dict[str, list[str]] = package[3]
    with get_db() as db:
      item_id: int = 0 # Keep track of the user. 
      for user in x_user_ids:
        user_insertion: item = item({
          'data': encase('"', f'data:{x_users[user]}'), 
          'did': encase('"', f'did:{user}'),
          'platform': '"platform:x"',
          'type': '"type:users"',
          'item_id': '"item_id:None"'
        })
        # Two-dimensional data fields have 'head' as their entry in the first dimension.
        db.execute('INSERT INTO first_dim_for_x (col_head_users, col_head_follows, col_head_posts) VALUES (?, ?, ?)',
                  [str(user_insertion), 'head', 'head'])
        db.commit()
      # Here we begin adding to the second dimension, starting with follows. 
      # The database format is exactly the same here as it is for
      # def bluesky(). Each person's follows or posts is printed to the database column,
      # all with an item_id unique to that person. The person in question can be
      # identified using the 'did' element within each entry. 
      for user in x_user_ids:
        follows_list = x_follows[user]
        posts_list = x_posts[user]
        len_follows_list = len(follows_list)
        len_posts_list = len(posts_list)
        # Like in Bluesky, we first insert from the list with the longest length. (say, `follows_list`).
        # To satisfy the 'not null' condition, the entries parallel to it from the
        # other list (say, `posts_list`) are 'None'.
        # Then, we update the list to change the 'None' to entries from `posts_list`.
        # Finally, if `posts_list` is longer than `follows_list`, we insert it only.
        if len_follows_list >= len_posts_list:
          for i in range(len_follows_list):
            # Insert for follows_list
            follows_insertion: item = item({
              'data': encase('"', f'data:{str(follows_list[i])}'), # if it is None, it will be put in like that
              'did': encase('"', f'did:{user}'), 
              'platform': '"platform:x"',
              'type': '"type:follows"',
              'item_id': encase('"', f'item_id:{str(item_id)}') 
            })
            db.execute("INSERT INTO second_dim_for_x (col_len_follows, col_len_posts, item_id) VALUES (?, ?, ?)",
                      [str(follows_insertion), '"None"', str(item_id)]) # To know which to update , we keep track of the item_id.
            db.commit()
          # Update posts_list
          for i in range(len_posts_list):
            posts_insertion: item = item({
              'data': encase('"', str(posts_list[i])),
              'did': encase('"', user),
              'platform': '"x"',
              'type': '"posts"',
              'item_id': encase('"', str(item_id))
            })
            db.execute('UPDATE second_dim_for_x SET col_len_posts = (?) WHERE item_id == (?)',
                        [str(posts_insertion), str(item_id)])
            db.commit()
        else: # len_posts_list > len_follows_list
          for i in range(len_posts_list):
            # Insert for posts_list
            posts_insertion: item = item({
              'data': encase('"', f'data:{str(posts_list[i])}'), # if it is None, it will be put in like that
              'did': encase('"', f'did:{user}'),
              'platform': '"platform:x"',
              'type': '"type:posts"',
              'item_id': encase('"', f'item_id:{str(item_id)}') 
            })
            db.execute("INSERT INTO second_dim_for_x (col_len_follows, col_len_posts, item_id) VALUES (?, ?, ?)",
                        ['"None"', str(posts_insertion), str(item_id)])
            db.commit()
          # Update for follows_list
          for i in range(len_follows_list):
            follows_insertion: item = item({
              'data': encase('"', f'data:{str(follows_list[i])}'),
              'did': encase('"', f'did:{user}'),
              'platform': '"platform:x"',
              'type': '"type:posts"',
              'item_id': encase('"', f'item_id:{str(item_id)}')
            })
            db.execute('UPDATE second_dim_for_x SET col_len_follows = (?) WHERE item_id == (?)',
                        [str(follows_insertion), str(item_id)])
            db.commit()
        item_id += 1
    return render_template('x.html', identifiers=x_user_ids)
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
    pornhub_length: int = 10
    package: list = get_pornhub(pornhub_length) # return, at most, 10 pornstars.
    video_search: list[requests.Response] = package[0] 
    pornstars: list[str] = package[1]
    url = "https://pornhub2.p.rapidapi.com/v2/video_by_id"
    # These are our return values. Each represent a column of the CSV we want to create with this
    # function.
    # Unlike X or Bluesky, the API we use doesn't store comment data. Only title and text.
    # First, we extract the video ID for each response. Then, we create another 
    # request with the ID. 
    video_ids: list[str] = []
    with get_db() as db:
      for i in range(pornhub_length):
        # We're extracting the video ID now.
        raw: dict[str, str] = video_search[i].json().get('data').get('videos')[i]
        video_id: str = raw['video_id']
        video_ids.append(video_id)
        # Now, we're searching for this video using its ID. 
        querystring = {"id":video_id,"thumbsize":"small"}
        headers = {
          "x-rapidapi-key": get_auth('pornhub_key.txt'),
          "x-rapidapi-host": "pornhub2.p.rapidapi.com",
          "Content-Type": "application/json"
        }
        response: requests.Response = requests.get(url, headers=headers, params=querystring)
        # Now it's possible for us to get the details of it.
        # We grab the title and tags. But remember, since tags is two-dimensional, we 
        # only insert head for that here and then get it later. 
        insertion: item = item({
          'data' : encase('"', f'video_id:{video_id}'),
          'did' : '"did:None"',
          'platform' : '"platform:pornhub"',
          'type' : '"type:video_id"',
          'item_id': encase('"', f'item_id:{str(i)}')
        })
        db.execute('INSERT INTO first_dim_for_pornhub (col_head_tags, col_head_title_text, col_head_pornstar) VALUES (?, ?, ?)',
                  ['head', str(insertion), encase('"', pornstars[i])])
    # Next, we handle the second dimension.
    # We use the ids gathered before to search for title and tags. 
    # We make a request for each iteration.
    with get_db() as db:
      item_id: int = 0
      for i in range(pornhub_length):
        # Now, we're searching for this video using its ID. 
        querystring = {"id":video_ids[i],"thumbsize":"small"}
        headers = {
          "x-rapidapi-key": get_auth('pornhub_key.txt'),
          "x-rapidapi-host": "pornhub2.p.rapidapi.com",
          "Content-Type": "application/json"
        }
        response: requests.Response = requests.get(url, headers=headers, params=querystring)
        tags: list[dict[str,str]] = response.json().get('data').get('video').get('tags')
        # For this video, we just extracted its title and a list of tags. Now, we insert
        # them into the database this way.
        for e in tags:
          tag_insertion: item = item({
            'data': encase('"', f'tag_name:{e.get('tag_name', '"None"')}'),
            'did': '"did:None"',
            'platform': '"platform:pornhub"',
            'type': '"type:tag"',
            'item_id': encase('"', f'item_id:{str(item_id)}')
          })
          db.execute('INSERT INTO second_dim_for_pornhub (col_len_tags) VALUES (?)',
                    [str(tag_insertion)])
          db.commit()
        item_id += 1
    return render_template('pornhub.html', identifiers='identifiers')
  return render_template('pornhub.html')

"""Functions for returning the csv."""

@app.route('/get_pornhub_csv', methods=['GET'])
def get_pornhub_csv():
  """Convert the database file into a csv. Tracks follows. 
  The csv represents an undirected and simple graph. Edge weight is 2."""
  # First, we open the database.
  # We are gathering a source and target for each row.
  # We gather a list; each element represents a single cell of the column
  # in question.
  with get_db() as db:
    cur = db.execute("SELECT col_head_title_text FROM first_dim_for_pornhub")
    f = cur.fetchall()
    l: list[str] = [row[0] for row in f]
    final: list[dict[str,str]] = []
    # So here we make that list. Each element resembles an insertion object
    # ,being a dict. 
    for e in l:
      final.append(extract(e))
  return render_template('bluesky.html')
