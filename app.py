from flask import Flask, render_template
import requests # pyright: ignore[reportMissingModuleSource]
import os, random
from utility.db_commands import get_db
from utility.classes import item
import utility.classes
import random, string

def get_auth(location: str) -> str:
  """Get an auth token or key from a hidden file."""
  with open(os.path.relpath("authorization/"+location, 'r')) as auth_file:
    ret: str = auth_file.read() 
    return ret
  return None


def make_token():
    """A token maker for the Pornhub API only.
    Made by Copilot 2026."""
    alphabet = string.digits + string.ascii_lowercase
    return ''.join(random.choice(alphabet) for _ in range(15))


"""Global API responses for Bluesky."""
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

"Global API responses for X."
x_users_url = "https://twitter-api45.p.rapidapi.com/screenname.php"
# Get 100 random users.
rest_ids: list[int] = []
x_length = 100
for i in range(x_length):
  rest_ids.append(random.randrange(1, 999999999))
x_users_responses: list[requests.Response] = []
for i in range(x_length):
  x_users_querystring = {"screenname":"","rest_id":rest_ids[i]} # the id overrides the screenname.
  x_users_headers = {
    "x-rapidapi-key": get_auth('x_authorization.txt'),
    "x-rapidapi-host": "twitter-api45.p.rapidapi.com",
    "Content-Type": "application/json"
  }
  # The user info.
  x_users_responses.append(requests.get(x_users_url, headers=x_users_headers, params=x_users_querystring))

screennames: list[str] = []
for i in range(x_length):
  screennames.append(x_users_responses[i].json().get('profile'))

# now we get follow data.
x_follows_responses: list[requests.Response] = []
x_post_responses: list[requests.Response] = []
for i in range(x_length):
  x_follows_url = "https://twitter-api45.p.rapidapi.com/following.php"
  x_follows_querystring = {"screenname":screennames[i]}
  x_follows_headers = {
    "x-rapidapi-key": get_auth('x_authorization.txt'),
    "x-rapidapi-host": "twitter-api45.p.rapidapi.com",
    "Content-Type": "application/json"
  }
  x_follows_responses.append(requests.get(x_follows_url, headers=x_follows_headers, params=x_follows_querystring))

  # now we get post data.
  x_post_url = "https://twitter-api45.p.rapidapi.com/tweet.php"
  x_post_querystring = {"id":rest_ids[i]}
  x_post_headers = {
    "x-rapidapi-key": get_auth('x_authorization.txt'),
    "x-rapidapi-host": "twitter-api45.p.rapidapi.com",
    "Content-Type": "application/json"
  }
  x_post_responses.append(requests.get(x_post_url, headers=x_post_headers, params=x_post_querystring))

# In conclusion, we now have (1) a list of responses for users, (2) a list of responses for follows,
# (3) a list of responses for posts. 

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


app = Flask(__name__)

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
  # These are our return values. Each represent a column of the CSV we want to create with this
  # function.
  # We also include 'identifiers'. This is the DID of users in question. It is used later.
  users: list[str] = []
  genders: list[str] = []
  follows: list[item] = []
  text: list[item] = []
  # This is a list of handles of users. 
  identifiers: list[str] = []
  # Now that we have a list of actors from global, we can search their feeds locally.
  posts_endpoint: str = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
  follows_endpoint: str = "https://api.bsky.app/xrpc/app.bsky.graph.getFollows"
  # Key: Handle of user in question
  # Value: URI of text from post.
  all_posts: dict[str, item] = {} 
  # Key: Handle of the user in question
  # Value: Handle of the followed user 
  all_follows: dict[str, item] = {}
  for actor in range(bluesky_limit): # type: ignore
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
      # insert an item.
      insertion: item = item()
      insertion.data = post_response.json().get('posts')[0].get('uri')
      insertion.platform = 'bluesky'
      insertion.did = identifier
      all_posts[identifier] = insertion 
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
      # Insert an item.
      insertion: item = item()
      insertion.data = follows_response.json().get('follows')[0].get('did')
      insertion.platform = 'bluesky'
      insertion.did = identifier
      all_follows[identifier] = insertion 
  # We gather all of the columns for the CSV at this point.
  # Those four columns were (1) actor, (2) gender, (2) perceived audience, (3) Perceived opinion.
  # We create four variables now, each of which represents a column
  for i in range(b_actors_params.get('limit')): # type: ignore
    users.append(actors.json().get('actors')[i].get('did'))
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
  #
  # We create 'insertions' instead of putting raw data.
  # This is important for the backend workings of the 3D database.
  # 
  # Because the users response was fetched outside of the function, we 
  # create the insertion for it here. We do the same for 'genders', which
  # does not need a third dimension unlike 'posts' and 'follows'. 
  with get_db() as db:
    for i in range(bluesky_length): # assume all of these lists are the same length
      insertion: item = item() 
      insertion.data = actors.json().get('actors')[i].get('displayName')
      insertion.did = actors.json().get('actors')[i].get('did') 
      insertion.platform = 'bluesky'
      insertion.type = 'user'
      db.execute('INSERT INTO second_dim_for_bluesky (col_head_users) VALUES (?)', utility.classes.to_string(insertion))
      db.execute('INSERT INTO second_dim_for_bluesky (col_head_follows) VALUES (?)', utility.classes.to_string(all_follows[identifiers[i]]))
      db.execute('INSERT INTO second_dim_for_bluesky (col_head_posts) VALUES (?)', utility.classes.to_string(all_posts[identifiers[i]]))
      db.commit()
    for i in range(bluesky_length):
      insertion: item = item() 
      insertion.data = actors.json().get('actors')[i].get('pronouns')
      insertion.did = actors.json().get('actors')[i].get('did') 
      insertion.platform = 'bluesky'
      insertion.type = 'user'
      db.execute('INSERT INTO second_dim_for_bluesky (col_head_genders) VALUES (?)', utility.classes.to_string(insertion))

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
  # We have a list of (1) user responses, (2) follows responses, and (3) post responses from above.
  users: list[item] = []
  follows: list[item] = []
  posts: list[item] = []
  for i in range(len(x_users_responses)):
    insertion: item = item()
    insertion.data = x_users_responses[i].json().get('name')
    insertion.did = x_users_responses[i].json().get('rest_id')
    insertion.platform = 'x'
    insertion.type = 'user'
    users.append(insertion)
  for i in range(len(x_follows_responses)):
    insertion: item = item()
    # Okay, this here is a list 
    # Here, we have just provided a reference to the data.
    # Then, you can insert every one of the list elements
    # into a database. 
    insertion.data = 'list_' + str(i)
    insertion.did = x_users_responses[i].json().get('rest_id')
    insertion.platform = 'x'
    insertion.type = 'follows'
    follows.append(insertion)
  for i in range(len(x_post_responses)):
    insertion: item = item()
    insertion.data = 'list_' + str(i)
    insertion.did = x_users_responses[i].json().get('rest_id')
    insertion.platform = 'x'
    insertion.type = 'follows'
    posts.append(insertion)
  with get_db() as db:
    for i in range(x_length): # assume all of these lists are the same length
      db.execute('INSERT INTO second_dim_for_x (col_head_users) VALUES (?)', utility.classes.to_string(users[i]))
      db.execute('INSERT INTO second_dim_for_x (col_head_follows) VALUES (?)', utility.classes.to_string(follows[i]))
      db.execute('INSERT INTO second_dim_for_x (col_head_posts) VALUES (?)', utility.classes.to_string(posts[i]))
      db.commit()
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
  title_text: list[item] = []
  for i in range(pornhub_length):
    raw: list[dict[str, str]] = pornhub_responses[i].json().get('data').get('video').get('tags')
    string_list: list[str] = []
    for element in raw:
      string_list.append(element.get('tag_name')) # pyright: ignore[reportArgumentType]
    insertion: item = item()
    insertion.data = string_list[0]     # this is arbitrary. We would open the third dimension here. 
    insertion.did = 'none'
    insertion.platform = 'pornhub'
    insertion.type = 'tags'
    tags.append(insertion)

    insertion: item = item()
    insertion.data = pornhub_responses[i].json().get('data').get('video').get('title') 
    insertion.did = 'none'
    insertion.platform = 'pornhub'
    insertion.type = 'title text'
    title_text.append(insertion)
  # Finally, we add these to the database.
  # We only add one tag per video, as this version currently does not
  # support more than 2 dimensions in the DB. 
  with get_db() as db:
    for i in range(pornhub_length):
      db.execute('INSERT INTO second_dim_for_pornhub (col_head_tags) VALUES (?)',
                [tags[i]])
      db.execute('INSERT INTO second_dim_for_pornhub (col_head_title_text) VALUES (?)',
                [title_text[i]])
      db.commit()
  return render_template('pornhub.html')
