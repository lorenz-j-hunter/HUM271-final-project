from flask import Flask, render_template, request
import requests # pyright: ignore[reportMissingModuleSource]

# All URL endpoints used.
# We use 'actors' to get a query of said actor's feed. 
actors_endpoint = "https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors"

# All endpoint parameters used.

actors_params: dict[str, str | int] = {
  "q" : "", # an empty string returns `general users`. 
  "limit" : 5 
}

# The responses created with these endpoints and their parameters.
actors: requests.Response = requests.get(
  actors_endpoint, actors_params
)

# Now that we have a list of actors, we will search their feed.
feeds_endpoint = "https://public.api.bsky.app/xrpc/app.bsky.feeds/getActorFeeds"
feeds_params: dict[str, str | int] = {
  "actor" : "",
  "limit" : 5
}

actors_feeds: requests.Response = requests.get(
  feeds_endpoint, feeds_params 
)

# Open the app
app = Flask(__name__)

print(actors.json())

@app.route('/', methods=['GET','POST'])
def main():
  """Open the main route for the app.

  In Bluesky, the text from any post in the JSON is arranged like so:
  feed > post > record > text

  If you want to traverse by feed/fetched stuff, then change the `[0]` here to whatever number you choose,
  provided it is less than `limit` in your params.

  If you want stuff other than the text, like the author, you can play with `get('post')`. 
  """
  text: list[str] = []
  for post in range(actors_params.get('limit')): # type: ignore
    # We gather all of the columns for the CSV at this point.
    # Those four columns were (1) actor, (2) gender, (2) feed, (3) Perceived opinion.
    # We create four variables now, each of which represents a column 
    actor = actors_feeds.json().get('feed', None)[post].get('creator').get('displayName')
    pronouns = actors_feeds.json().get('feed', None)[post].get('creator').get('pronouns')
    feed = actors_feeds.json().get('feed', None)[post].get('creator').get('pronouns')
    opinion = actors_feeds.json().get('feed', None)[post].get('creator').get('associated').get('chat')
    text.append(opinion.get('text'))
  return render_template('main.html', text=text)