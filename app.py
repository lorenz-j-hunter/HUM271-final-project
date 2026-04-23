from flask import Flask, render_template, request
import requests # pyright: ignore[reportMissingModuleSource]

# All URL endpoints used.
url = "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=mrsbettybowers.bsky.social"

getActors = "https://public.api.bsky.app/xrpc/app.bsky.actor.searchActors"

# All endpoint parameters used.
params = {
  "limit" : 1
}

getActorsParams = {
  "q" : "", # an empty string returns `general users`. 
  "limit" : 5 
}

# The responses created with these endpoints and their parameters.
response = requests.get(
  url, params
)

actorsResponse = requests.get(
  getActors, getActorsParams
)

# Open the app
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def main():
  """Open the main route for the app."""
  posts = response.json().get('feed', None)[0].get('post', 'There was no post.').get('record', 'There was no record.')
  text = posts.get('text')
  print(text)
  return render_template('main.html', response=response.json())