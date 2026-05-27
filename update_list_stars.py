import requests, math
import app as webscraping

"""Create a database of all stars.

This is meant to be run as a file, not store functions."""

with webscraping.app.app_context():
  webscraping.init_db('list_of_stars')

# Here, we just want to get the total number.
# That's `total_stars`.

url = "https://pornhub2.p.rapidapi.com/v2/stars_detailed"

querystring = {"offset":"0","limit":"1000"}

headers = {
  "x-rapidapi-key": "3f1b94c125msh54ccb0fd424ce04p14eac0jsn91eb994c3dfd",
  "x-rapidapi-host": "pornhub2.p.rapidapi.com",
  "Content-Type": "application/json"
}

response = requests.get(url, headers=headers, params=querystring)

total_stars: int = response.json().get('total_count', -1) 

if total_stars == -1:
  raise TypeError('List of stars could not be created.')

# Now, we gather all of those stars.
# They get stored in a list of responses.

raw: list[dict[str,str]] = []
for i in range(int(math.ceil(total_stars/1000))):

  url = "https://pornhub2.p.rapidapi.com/v2/stars_detailed"

  querystring = {"offset":str(i*1000),"limit":"1000"}

  headers = {
    "x-rapidapi-key": "3f1b94c125msh54ccb0fd424ce04p14eac0jsn91eb994c3dfd",
    "x-rapidapi-host": "pornhub2.p.rapidapi.com",
    "Content-Type": "application/json"
  }

  response = requests.get(url, headers=headers, params=querystring)
  raw = raw + response.json().get('stars')

# Then, the names of those responses are stored in their own list.

stars: list[str] = []
for response in raw:
  if response.get('star_name'):
    stars.append(response.get('star_name', 'None')) # This 'None' should never be reached.

# Now, we insert them to the database.
with webscraping.app.app_context():
  db = webscraping.get_db()
  for star in stars:
    db.execute('INSERT INTO list_of_stars (star) VALUES (?)', [star])
    db.commit()
  db.close()