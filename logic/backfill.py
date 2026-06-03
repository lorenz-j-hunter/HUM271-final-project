from sqlite3 import dbapi2 as sqlite3
import requests

async def backfill(db_path):
  """Backfill the 'profile' table from 'jetstream.sql'
  using REST API."""
  db = sqlite3.connect(db_path, check_same_thread=False)
  db.row_factory = sqlite3.Row
  # get list of unique users
  f = db.execute('SELECT DISTINCT follower FROM follows').fetchall() 
  followers: list[str] = [row[0] for row in f]
  #
  endpoint = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfiles"
  params: dict[str, list[str]] = {
    "actors" : followers,
  }
  response = requests.get(endpoint, params)
  profiles = response.json().get('profiles')
  # fill database with profile data
  for profile in profiles:
    f = db.execute('SELECT rkey FROM profiles WHERE did = (?)', [profile.get('did')]).fetchone()
    rkey = [row[0] for row in f]
    db.execute('UPDATE profiles SET did = (?), display_name = (?), avatar_cid = (?),'
               'banner_cid = (?), website = (?), pronouns = (?), created_at = (?)'
               'WHERE rkey = (?)',
               [profile.get('did'), profile.get('displayName'), profile.get('avatar'),
                profile.get('banner'), profile.get('website'), profile.get('pronouns'),
                profile.get('createdAt'), rkey]) 
    db.commit()
  # tell that worker is done. 
  db.execute('UPDATE worker_done SET value = (?) WHERE value == (?)', ['true', 'false'])
  print('Completed backfill')
  db.commit()
  db.close()
