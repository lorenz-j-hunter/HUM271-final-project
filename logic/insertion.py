from logic.rest_request import get_bluesky, get_pornhub, get_x
import requests, os
from utils.utils import get_age
from utils.classes import compound, FieldError
from sqlite3 import dbapi2 as sqlite3
from logic.csv import get_bluesky_csv 
from logic.websocket import loop, loop_runner


def clear_bsky(db_path):
  """Clear the whole Bluesky database."""
  db = sqlite3.connect(db_path, check_same_thread=False)
  db.row_factory = sqlite3.Row
  db.execute('DELETE FROM first_dim_for_bluesky')
  db.execute('DELETE FROM second_dim_for_bluesky')
  db.commit()
  db.close()



async def bsky(db_path, params={'bluesky_length': 10, 'limit': 100, 'querystring': "a"}):
  """Add response data to the Bluesky database table."""
  # unpack params
  bluesky_length = params['bluesky_length'] + 1
  follows_limit = 100 if not params['limit'] else int(params['limit'])
  posts_limit = 100 if not params['limit'] else int(params['limit'])
  posts_query = "a" if not params['querystring'] else params['querystring']
  columns = {
      'age': None,
      'pronouns': None 
    } if not params['columns'] else params['columns']
  # connect database
  db = sqlite3.connect(db_path, check_same_thread=False)
  db.row_factory = sqlite3.Row
  # get requests
  actors: dict[str, list[dict[str, str]]] = get_bluesky(bluesky_length)
  # Now we define some common variables.
  # `identifiers` is a list of handles of users.
  # This is on same dimension as 'bluesky_length' but not for 'follows_limit'.
  identifiers: list[str] = []
  posts_endpoint: str = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
  follows_endpoint: str = "https://api.bsky.app/xrpc/app.bsky.graph.getFollows"
  # Key: Handle of user in question
  # Value: URI of text from post.
  all_posts: dict[str, list[str]] = {}
  # Key: Handle of the user in question
  # Value: List of handles of follows.
  all_follows: dict[str, list[str]] = {}
  # Here, we traverse the thing by actor.
  # We separate actors' handles from the json first to do this.
  for e in actors['actors']:
    identifiers.append(e['handle'])
  for identifier in identifiers:
    # Here, we gather all post data of the user in question.
    # It is stored in a dict; the DID of the user in question is
    # the key and the corresponding *list* of posts is the value.
    posts_params: dict[str, str | int] = {
      "q" : posts_query,
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
    insertion_list: list[str] = []
    for i in range(posts_limit):
      # insert a post uri.
      try:
        insertion_list.append(post_response.json().get('posts')[i].get('uri'))
      except IndexError:
        break
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
      # insert the user ID of the follow.
      insertion_list: list[str] = []
      for i in range(follows_limit):
        try:
          insertion_list.append(follows_response.json().get('follows')[i].get('did'))
        except IndexError:
          break
      all_follows[identifier] = insertion_list 
    else: # In this case, we still have to fill all_follows with something.
      all_follows[identifier] = [] 
  # Finally, we add these columns to a database, actor by actor.
  # We first insert to the first dimension here, then move onto the second dimension.
  for actor in range(bluesky_length): 
    age_months: int = get_age(actors['actors'][actor].get('createdAt', 'None'))
    db.execute('INSERT INTO first_dim_for_bluesky (name, did, age_months, pronouns) VALUES (?, ?, ?, ?)',
                [actors['actors'][actor].get('displayName', 'None'),
                actors['actors'][actor].get('did', 'None'),
                age_months,
                actors['actors'][actor].get('pronouns', 'None')])
    # Now we add to the second dimension for follows and posts. 
    # First we insert into both columns for follows. Then, we update the rows
    # that have been filled with posts.
    # follows:
    f_insertion_list: list[str] = all_follows[identifiers[actor]]
    for e in range(len(f_insertion_list)):
      db.execute('INSERT INTO second_dim_for_bluesky (follows, posts, item_id) VALUES (?, ?, ?)',
                [f_insertion_list[e],
                  'None',
                  str(actor)])
    # posts:
    f_insertion_list_len: int = len(all_follows[identifiers[actor]])
    p_insertion_list: list[str] = all_posts[identifiers[actor]]
    p_insertion_list_len: int = len(p_insertion_list)
    # If there are more follows than posts, there is a case for that. 
    # likewise for posts > follows and posts == follows.
    if p_insertion_list_len > f_insertion_list_len:
      for e in range(f_insertion_list_len):
        db.execute('UPDATE second_dim_for_bluesky SET posts = (?) WHERE item_id == (?)',
                    [p_insertion_list[e], e])
      for e in range(len(p_insertion_list) - f_insertion_list_len):
        db.execute('INSERT INTO second_dim_for_bluesky (follows, posts, item_id) VALUES (?, ?, ?)',
                    ['None',
                      p_insertion_list[e],
                      str(actor)])
    elif f_insertion_list_len > p_insertion_list_len | f_insertion_list_len == p_insertion_list_len:
      for e in range(p_insertion_list_len):
        db.execute('UPDATE second_dim_for_bluesky SET posts = (?) WHERE item_id == (?)',
                    [p_insertion_list[e], e])
  # Create the csv. This downloads it to their computer.
  get_bluesky_csv(db_path, columns)
  # Finally, we let the state know this operation is complete
  # and stop the thread (loop.stop()).
  print('Completed request, stopping worker')
  db.execute('UPDATE worker_done SET value = (?) WHERE value = (?)', ['true', 'false']) 
  db.commit()
  db.close()

def x(db, x_length=10):
  """Add response data to the X database table."""
  # We have dictionaries of (1) user responses, (2) follows responses, and (3) post responses from above.
  # Now we (1) add user responses data to first_dim, (2) add follows/post data to second dim.
  # Unpacking... We get the responses here.
  package: list = get_x(x_length) 
  x_user_ids: list[str] = package[0] 
  x_users: dict[str, dict[str,str]] = package[1] 
  x_follows: dict[str, list[str]] = package[2] 
  x_posts: dict[str, list[str]] = package[3]
  for did in x_user_ids:
    # Two-dimensional data fields have 'head' as their entry in the first dimension.
    db.execute('INSERT INTO first_dim_for_x (name, did, age, affiliation, verified) VALUES (?, ?, ?, ?)',
              [x_users[did]['username'],
                did,
                get_age(x_users[did]['created_at']),
                x_users[did]['affiliation'],
                x_users[did]['verified']])
    db.commit()
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
        db.execute("INSERT INTO second_dim_for_x (follows, posts, item_id) VALUES (?, ?, ?)",
                  [follows_list[i], 'None', str(item_id)]) # To know which to update , we keep track of the item_id.
        db.commit()
      # Update posts_list
      for i in range(len_posts_list):
        db.execute('UPDATE second_dim_for_x SET posts = (?) WHERE item_id == (?)',
                    [posts_list[i], str(item_id)])
        db.commit()
    else: # len_posts_list > len_follows_list
      for i in range(len_posts_list):
        # Insert for posts_list
        db.execute("INSERT INTO second_dim_for_x (follows, posts, item_id) VALUES (?, ?, ?)",
                    ['None', str(posts_list[i]), str(item_id)])
        db.commit()
      # Update for follows_list
      for i in range(len_follows_list):
        db.execute('UPDATE second_dim_for_x SET follows = (?) WHERE item_id == (?)',
                    [str(follows_list[i]), str(item_id)])
        db.commit()
    item_id += 1

def pornhub(db, request, pornhub_length=10) -> None | FieldError:
  """Add response data to the Pornhub database table."""
  # Process these inputs from user. Used to get the package. 
  pornstars_arg = request.args.get('pornstars')
  if pornstars_arg == '':
    pornstars_arg = None
  tags_arg = request.args.get('tags')
  if tags_arg == '':
    tags_arg = None
  # Get the package from make_request.
  package: list = get_pornhub(
    pornhub_length,
    pornstars_arg=pornstars_arg,
    tags=tags_arg
  )
  video_search: list[compound] = package[0]
  pornstars = package[1]
  if pornstars[0] == 'invalid-pornstar':
    return FieldError('Invalid request field.') 
  url = "https://pornhub2.p.rapidapi.com/v2/video_by_id"
  # These are our return values. Each represent a column of the CSV we want to create with this
  # function.
  # Unlike X or Bluesky, the API we use doesn't store follow/profile data. Only title and text.
  # We might normally crawl follower graphs, but we cant do that here in other words.
  # First, we extract the video ID for each response. Then, we create another 
  # request with the ID. 
  video_ids: list[str] = []
  for i in range(pornhub_length):
    # We're extracting the video ID now. We encased each `video_search` entry in;
    # now we must convert each to a dict.
    response: requests.Response = video_search[i].get('response') # pyright: ignore[reportAssignmentType]
    pornstar: str = video_search[i].get('comment') # pyright: ignore[reportAssignmentType]
    raw: dict[str, str] = response.json().get('data').get('videos')[i]
    video_id: str = raw['video_id']
    title: str = raw['title']
    views: int = int(raw['views'])
    rating: str = str(raw['rating'])
    video_ids.append(video_id)
    # Now, we're searching for this video using its ID. 
    querystring = {"id":video_id,"thumbsize":"small"}
    headers = {
      "x-rapidapi-key": os.environ['PORNHUB_KEY'],
      "x-rapidapi-host": "pornhub2.p.rapidapi.com",
      "Content-Type": "application/json"
    }
    response: requests.Response = requests.get(url, headers=headers, params=querystring)
    # Now it's possible for us to get the details of it.
    # We grab the title and tags. But remember, since tags is two-dimensional, we 
    # only insert head for that here and then get it later. 
    db.execute('INSERT INTO first_dim_for_pornhub (title, pornstar, views, rating, video_id) VALUES (?, ?, ?, ?, ?)',
              [title, pornstar, views, rating, video_id])
  # Next, we handle the second dimension.
  # We use the ids gathered before to search for title and tags. 
  # We make a request for each iteration.
  for item_id in range(pornhub_length):
    # Now, we're searching for this video using its ID. 
    querystring = {"id":video_ids[item_id],"thumbsize":"small"}
    headers = {
      "x-rapidapi-key": os.environ['PORNHUB_KEY'],
      "x-rapidapi-host": "pornhub2.p.rapidapi.com",
      "Content-Type": "application/json"
    }
    response: requests.Response = requests.get(url, headers=headers, params=querystring)
    tags: list[dict[str,str]] = response.json().get('data').get('video').get('tags')
    # For this video, we just extracted its title and a list of tags. Now, we insert
    # them into the database this way.
    for e in tags:
      db.execute('INSERT INTO second_dim_for_pornhub (item_id, tags) VALUES (?, ?)',
                [item_id+1, e.get('tag_name', 'None')])
      db.commit()
