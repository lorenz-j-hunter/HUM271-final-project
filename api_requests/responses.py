import requests, time, random # pyright: ignore[reportMissingModuleSource]
from utility.utilities import make_token, get_auth



def get_pornhub() -> list[int | list[requests.Response]]:
  """API responses for Pornhub.
  Return [pornhub_length, pornhub_responses], where `pornhub_length` is the number of videos
  that were requested and `pornhub_responses` is `list[requests.Response]`."""
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
    assert pornhub_responses[i].status_code == 200
  except AssertionError:
    print(f"pornhub_responses[{i}].status_code == {pornhub_responses[i].status_code}") 
  return [pornhub_length, pornhub_responses]
