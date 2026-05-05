import requests, time, os # pyright: ignore[reportMissingModuleSource]
from utility.utilities import make_token


def get_bluesky() -> list[requests.Response | int]:
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
  return [bluesky_length, actors]



def get_x() -> list[list[str] | dict[str, str] | dict[str, list]]:
  """Global API responses for X."""
  # Just so you know, we only get these in order to get author ids. 
  x_posts_url = "https://api.x.com/2/tweets/search/all"
  x_posts_headers = {"Authorization": f"Bearer {os.environ['X_BEARER_TOKEN']}"}
  x_posts_params = {
    "query": "lang:en a e i o u",
    "start_time": "2020-01-01T00:00:00Z",
    "end_time": "2026-01-01T00:00:00Z",
    "max_results": 10,
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
    headers = {"Authorization": f"Bearer {os.environ['X_BEARER_TOKEN']}"}
    params = {"user.fields": ['username']}
    response = requests.get(url, headers=headers, params=params)
    x_users[id] = response.json().get('data').get('username')
  # Now, we get follow data.
  x_follows: dict[str, list[str]] = {}
  for id in x_user_ids:
    # Make the request.
    url = f"https://api.x.com/2/users/{id}/following"
    headers = {"Authorization": f"Bearer {os.environ['X_BEARER_TOKEN']}"} 
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
    headers = {"Authorization": f"Bearer {os.environ['X_BEARER_TOKEN']}"}
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




def get_pornhub() -> list[int | list[requests.Response]]:
  """Global API responses for Pornhub."""
  url = "https://pornhub2.p.rapidapi.com/v2/video_by_id"
  pornhub_length = 100
  pornhub_responses: list[requests.Response] = []
  for i in range(pornhub_length):
    querystring = {"id":make_token(),"thumbsize":"small"}
    headers = {
      "x-rapidapi-key": os.environ['PORNHUB_KEY'],
      "x-rapidapi-host": "pornhub2.p.rapidapi.com",
      "Content-Type": "application/json"
    }
    pornhub_responses.append(requests.get(url, headers=headers, params=querystring))
  try:
    assert pornhub_responses[i].status_code == 200
  except AssertionError:
    print(f"pornhub_responses[{i}].status_code == {pornhub_responses[i].status_code}") 
  return [pornhub_length, pornhub_responses]
