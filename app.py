import os, requests, csv  # pyright: ignore[reportMissingModuleSource
from utils.classes import item
from flask import Flask, render_template, g, request
from sqlite3 import dbapi2 as sqlite3
from utils.utils import get_auth, encase, extract
from logic import originals as responses

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


"""Begin endpoints for html pages"""


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
    actors: dict[str, list[dict[str, str]]] = responses.get_bluesky(bluesky_length) 
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
          'data' : encase('#', f'data:{post_response.json().get('posts')[i].get('uri')}'),
          'did' : encase('#', f'did:{identifier}'),
          'platform' : encase('#', 'platform:bluesky'),
          'type' : encase('#', 'type:posts'),
          'item_id': encase('#', f'item_id:{str(i)}')
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
            'data' : encase('#', f'data:{follows_response.json().get('follows')[i].get('did')}'),
            'did' : encase('#', f'identifier:{identifier}'),
            'platform' : encase('#', 'platform:bluesky'),
            'type' : encase('#', 'type:follows'),
            'item_id': encase('#', f'item_id:{str(i)}')
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
          'data' : encase('#', f'data:{actors['actors'][actor].get('displayName', 'None')}'), 
          'did' : encase('#', f'did:{actors['actors'][actor].get('did', 'None')}'),
          'platform' : encase('#', 'platform:bluesky'),
          'type' : encase('#', 'type:user'),
          'item_id': encase('#', f'item_id:{str(actor)}')
        }) 
        db.execute('INSERT INTO first_dim_for_bluesky (users) VALUES (?)',
                  [str(insertion)])
        db.commit()
        # Now we add to the second dimension for follows and posts. 
        # First we insert into both columns for follows. Then, we update the rows
        # that have been filled with posts.
        # Finally, to cover all cases, we may insert after that, too.
        for _ in range(follows_limit):
          f_insertion_list: list[item] = all_follows[identifiers[actor]]
          for e in range(len(f_insertion_list)):
            db.execute('INSERT INTO second_dim_for_bluesky (follows, posts) VALUES (?, ?)',
                      [str(f_insertion_list[e]), 'None'])
            db.commit()
        for _ in range(posts_limit):
          f_insertion_list_len: int = len(all_follows[identifiers[actor]])
          p_insertion_list: list[item] = all_posts[identifiers[actor]]
          # We first update what has already been inserted.
          for e in range(f_insertion_list_len):
            db.execute('UPDATE second_dim_for_bluesky SET posts = (?) WHERE id == (?)',
                        [str(p_insertion_list[e]), e])
            db.commit()
          # Then, we continue to insert if there are more posts than follows. 
          if len(p_insertion_list) > f_insertion_list_len:
            for e in range(f_insertion_list_len, len(p_insertion_list)):
              db.execute('INSERT INTO second_dim_for_bluesky (follows, posts) VALUES (?, ?)',
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
    package: list = responses.get_x(10) # return, at most, 10 responses.
    x_user_ids: list[str] = package[0] 
    x_users: dict[str, str] = package[1] 
    x_follows: dict[str, list[str]] = package[2] 
    x_posts: dict[str, list[str]] = package[3]
    with get_db() as db:
      item_id: int = 0 # Keep track of the user. 
      for user in x_user_ids:
        user_insertion: item = item({
          'data': encase('#', f'data:{x_users[user]}'), 
          'did': encase('#', f'did:{user}'),
          'platform': encase('#', 'platform:x'),
          'type': encase('#', 'type:users'),
          'item_id': encase('#', f'item_id:{item_id}')
        })
        # Two-dimensional data fields have 'head' as their entry in the first dimension.
        db.execute('INSERT INTO first_dim_for_x (users) VALUES (?)',
                  [str(user_insertion)])
        db.commit()
        item_id += 1
      # Here we begin adding to the second dimension, starting with follows. 
      # The database format is exactly the same here as it is for
      # def bluesky(). Each person's follows or posts is printed to the database column,
      # all with an item_id unique to that person. The person in question can be
      # identified using the 'did' element within each entry. 
      item_id: int = 0
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
              'data': encase('#', f'data:{str(follows_list[i])}'), # if it is None, it will be put in like that
              'did': encase('#', f'did:{user}'), 
              'platform': encase('#', 'platform:x'),
              'type': encase('#', 'type:follows'),
              'item_id': encase('#', f'item_id:{str(item_id)}') 
            })
            db.execute("INSERT INTO second_dim_for_x (follows, posts, item_id) VALUES (?, ?, ?)",
                      [str(follows_insertion), '"None"', str(item_id)]) # To know which to update , we keep track of the item_id.
            db.commit()
          # Update posts_list
          for i in range(len_posts_list):
            posts_insertion: item = item({
              'data': encase('#', str(posts_list[i])),
              'did': encase('#', user),
              'platform': encase('#', 'x'),
              'type': encase('#', 'posts'),
              'item_id': encase('#', str(item_id))
            })
            db.execute('UPDATE second_dim_for_x SET posts = (?) WHERE item_id == (?)',
                        [str(posts_insertion), str(item_id)])
            db.commit()
        else: # len_posts_list > len_follows_list
          for i in range(len_posts_list):
            # Insert for posts_list
            posts_insertion: item = item({
              'data': encase('#', f'data:{str(posts_list[i])}'), # if it is None, it will be put in like that
              'did': encase('#', f'did:{user}'),
              'platform': encase('#', 'platform:x'),
              'type': encase('#', 'type:posts'),
              'item_id': encase('#', f'item_id:{str(item_id)}') 
            })
            db.execute("INSERT INTO second_dim_for_x (follows, posts, item_id) VALUES (?, ?, ?)",
                        ['"None"', str(posts_insertion), str(item_id)])
            db.commit()
          # Update for follows_list
          for i in range(len_follows_list):
            follows_insertion: item = item({
              'data': encase('#', f'data:{str(follows_list[i])}'),
              'did': encase('#', f'did:{user}'),
              'platform': encase('#', 'platform:x'),
              'type': encase('#', 'type:posts'),
              'item_id': encase('#', f'item_id:{str(item_id)}')
            })
            db.execute('UPDATE second_dim_for_x SET follows = (?) WHERE item_id == (?)',
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
    package: list = responses.get_pornhub(pornhub_length) # return, at most, 10 pornstars.
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
          'data' : encase('#', f'video_id:{video_id}'),
          'did' : '"did:None"',
          'platform' : '"platform:pornhub"',
          'type' : '"type:video_id"',
          'item_id': encase('#', f'item_id:{str(i)}')
        })
        db.execute('INSERT INTO first_dim_for_pornhub (title, pornstar) VALUES (?, ?)',
                  [str(insertion), encase('#', pornstars[i])])
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
            'data': encase('#', f'tag_name:{e.get('tag_name', '"None"')}'),
            'did': encase('#', 'did:None'),
            'platform': encase('#', 'platform:pornhub'),
            'type': encase('#', 'type:tag'),
            'item_id': encase('#', f'item_id:{str(item_id)}')
          })
          db.execute('INSERT INTO second_dim_for_pornhub (tags) VALUES (?)',
                    [str(tag_insertion)])
          db.commit()
        item_id += 1
    return render_template('pornhub.html', identifiers='identifiers')
  return render_template('pornhub.html')

"""Functions for returning the csv."""

@app.route('/get_bluesky_csv', methods=['GET'])
def get_bluesky_csv():
  """Convert the database file into a csv. 
  The csv represents an undirected and simple graph."""  
  consolidated: list[dict[str,list[str]]] = []
  with get_db() as db:
    # We open the first dimension here. The only column opened is the one
    # with one dimension.
    cur = db.execute('SELECT users FROM first_dim_for_bluesky')
    f = cur.fetchall()
    user_data: list[str] = [row[0] for row in f]
    # Now, we extract from this. We put each cell in a dict.
    # This is so that the data inside can be used to gather data
    # on the user later.
    for item_id in range(len(user_data)):
      cur = db.execute('SELECT follows, posts FROM second_dim_for_bluesky WHERE id == (?)',
                       [item_id])
      f = cur.fetchall()
      follows: list[str] = [row[0] for row in f]
      posts: list[str] = [row[1] for row in f]
      consolidated.append(dict({
        'datum': [str(item(extract(user_data[item_id])))],
        'follows': follows,
        'posts': posts
      }))
  # We write to the file now.
  # The mapping is surjective if the codomain is 'users' and domain is 'follows/posts', so
  # we loop by user and then insert all of their follows or posts. 
  with open('../csvfiles/bluesky.csv', 'w', newline='\n') as csvfile:
    field_names = ['user', 'follows', 'posts']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for item_id in range(len(user_data)):
      follows: list[str] = consolidated[item_id].get('follows', [])
      posts: list[str] = consolidated[item_id].get('posts', [])
      # case 1: number of follows > number of posts
      if len(follows) > len(posts):
        for i in range(len(posts)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': follows[i].split('#_#')[0].strip('#'),
            'posts': posts[i].split('#_#')[0].strip('#')
          })
        for i in range(len(posts), len(follows)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': follows[i].split('#_#')[0].strip('#'),
            'posts': 'None' 
          })
      # case 2: number of follows < number of posts
      elif len(posts) > len(follows):
        for i in range(len(follows)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': follows[i].split('#_#')[0].strip('#'),
            'posts': posts[i].split('#_#')[0].strip('#')
          })
        for i in range(len(follows), len(posts)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': 'None',
            'posts': posts[i].split('#_#')[0].strip('#')

          })
      # case 3: number of follows == number of posts
      elif len(posts) == len(follows):
        for i in range(len(follows)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': follows[i].split('#_#')[0].strip('#'),
            'posts': posts[i].split('#_#')[0].strip('#')
          })
  return render_template('bluesky.html') 

@app.route('/get_x_csv', methods=['GET'])
def get_x_csv():
  """Convert the database file into a csv. 
  The csv represents an undirected and simple graph.""" 
  # We first open the first dimension and gather the user data only.
  # Because the other two columns (follows and posts) are two-dimensional,
  # they will be fetched in a different scope.
  consolidated: list[dict[str,list[str]]] = []
  with get_db() as db:
    cur = db.execute('SELECT users FROM first_dim_for_x') 
    f = cur.fetchall()
    user_data: list[str] = [row[0] for row in f]
    # Now we do get follows and posts.
    # We want each list of follows and posts to still be associated with the user
    # in question for this data type, so we will append a list do 
    cur = db.execute('SELECT follows, posts FROM second_dim_for_x')
    f = cur.fetchall()
    follows_data: list[str] = []
    posts_data: list[str] = []
    for datum in user_data:
      user_item_id: str = datum.split('#_#')[4].strip('#')
      for row in f:
        follow: item = item(extract(row[0])) #keyError here
        post: str = row[1]
        # Only in the case that the user is the one we want to get follows, posts from do we
        # fetch them, is what this means. For each user, we loop through the entire second_dim
        # database. Each time, we pick the rows which have the user's item_id on them.
        if follow.get('item_id') == user_item_id:
          follows_data.append(str(follow))
          posts_data.append(str(post))
      # Now, we add these newly populated lists `follows_data`, etc into the `consolidated`. 
      consolidated.append(dict({
        'datum': [str(item(extract(datum)))],
        'follows': follows_data,
        'posts': posts_data
      }))
  # Now it comes down to making a csv out of this extracted and consolidated data.
  # For each user, we list all follows and posts. 
  # This is a surjective operation, and most of the rows for column 'users' will be copies.
  # If there are more posts than follows, the `follows` column will have row 'None' once
  # all of the follows have been printed. Likewise if there are more follows than posts. 
  # Now, we open a flat file and insert to it. 
  with open('../csvfiles/x.csv', 'w', newline='\n') as csvfile:
    field_names = ['user', 'did', 'follows', 'posts']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for elem in consolidated:
      # Here, we need to add a for loop. This will loop through the follows/posts.
      # For each follow/post, we write to the file.
      # Case 1: Number of user's follows > number of user's posts.
      if len(elem['follows']) > len(elem['posts']):
        for i in range(len(elem['posts'])):
          writer.writerow({
            'user': elem.get('datum')[0].split('#_#')[0].strip('#'),  # type: ignore
            'did': elem.get('datum')[0].split('#_#')[1].strip('#'),  # pyright: ignore[reportOptionalSubscript]
            'follows': elem['follows'][i].split('#_#')[0].strip('#'),
            'posts': elem['posts'][i].split('#_#')[0].strip('#')
          })
        for i in range(len(elem['posts']), len(elem['follows'])):
          writer.writerow({
            'user': elem.get('datum').split('#_#')[0].strip('#'), # type: ignore
            'did': elem.get('datum').split('#_#')[1].strip('#'), # type: ignore
            'follows': elem['follows'][i],
            'posts': '"None"' 
          })
      # case 2: Number of user's posts > number of user's follows
      elif len(elem['posts']) > len(elem['follows']):
        for i in range(len(elem['follows'])):
          writer.writerow({
            'user': elem.get('datum').split('#_#')[0].strip('#'), # type: ignore
            'did': elem.get('datum').split('#_#')[1].strip('#'), # type: ignore
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
        for i in range(len(elem['posts']), len(elem['follows'])):
          writer.writerow({
            'user': elem.get('datum').split('#_#')[0].strip('#'), # type: ignore
            'did': elem.get('datum').split('#_#')[1].strip('#'), # type: ignore
            'follows': '"None"',
            'posts': elem['posts'][i] 
          })
      # case 3: Number of user's posts == number of user's follows
      else:
        for i in range(len(elem['follows'])):
          writer.writerow({
            'user': elem.get('datum').split('#_#')[0].strip('#'), # type: ignore
            'did': elem.get('datum').split('#_#')[1].strip('#'), # type: ignore
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
  return render_template('x.html')

@app.route('/get_pornhub_csv', methods=['GET'])
def get_pornhub_csv():
  """Convert the database file into a csv. 
  The csv represents an undirected and simple graph."""
  # First, we open the database.
  # We are gathering a source and target for each row.
  # We gather a list; each element represents a single cell of the column
  # in question.
  consolidated: list[dict[str,str]] = []
  with get_db() as db:
    # We first get the video details...
    cur = db.execute("SELECT title, pornstar FROM first_dim_for_pornhub")
    f = cur.fetchall()
    video_data: list[str] = [row[0] for row in f]
    pornstar: list[str] = [row[1] for row in f]
    # So here we make that list. Each element resembles an insertion object
    # being a dict. 
    for i in range(len(video_data)):
      pre: dict[str,str] = extract(video_data[i])
      pre['pornstar'] = pornstar[i]  
      consolidated.append(pre)
  # Now, we open a flat file and insert to it. 
  with open('../csvfiles/pornhub.csv', 'w', newline='\n') as csvfile:
    field_names = ['video_id', 'did', 'platform', 'type', 'item_id', 'pornstar']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for row in consolidated:
      writer.writerow(row)
  return render_template('pornhub.html')
