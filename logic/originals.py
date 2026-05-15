import requests, time # type: ignore
from utils.utils import get_auth

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
  print('here')
  actors_list: list[requests.Response] = []
  while len(actors_list) <= bluesky_length:
    params: dict[str, str | int] = {
      "q" : 'a',
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

