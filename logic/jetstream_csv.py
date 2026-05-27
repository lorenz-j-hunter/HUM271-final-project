from flask import render_template
from sqlite3 import dbapi2 as sqlite3
import csv, os

def get_jetstream_csv(db_path):
  """Populate the csv file for the jetstream"""
  db = sqlite3.connect(db_path, check_same_thread=False)
  db.row_factory = sqlite3.Row
  # Determine if its follow or post
  cur = db.execute('SELECT id FROM jetstream_post')
  f = cur.fetchall()
  ids: list[int]= [row[0] for row in f]
  # i.e. if 'posts' was selected 
  line: list[dict[str,str]] = []
  posts: bool = len(ids) > 1
  if posts:
    # First, retrieve the data from the database.
    cur = db.execute('SELECT type, text, created_at FROM jetstream_post')
    f = cur.fetchall()
    types: list[str] = [row[0] for row in f]
    text: list[str] = [row[1] for row in f]
    created_at: list[str] = [row[2] for row in f]
    # aggregate into 'posts'
    for i in range(len(types)): # can be any of the columns
      line.append(dict({
        'type': types[i],
        'text': text[i],
        'created_at': created_at[i]
      }))
  # i.e. if 'follow' was selected
  elif not posts:
    # First, retrieve the data from the database.
    cur = db.execute('SELECT type, target, origin, created_at FROM jetstream_follow')
    f = cur.fetchall()
    types: list[str] = [row[0] for row in f]
    target: list[str] = [row[1] for row in f]
    origin: list[str] = [row[2] for row in f]
    created_at: list[str] = [row[3] for row in f]
    # aggregate into 'posts'
    for i in range(len(types)): # can be any of the columns
      line.append(dict({
        'type': types[i],
        'target': target[i],
        'origin': origin[i],
        'created_at': created_at[i]
      }))
  # create the csv with aggregated data.
  with open(os.path.relpath('../csvfiles/bsky-jetstream.csv'), 'w', newline='\n') as csvfile:
    if posts: 
      field_names = ['type', 'text', 'created_at']
      writer = csv.DictWriter(csvfile, fieldnames=field_names)
      writer.writeheader()
      for post in line:
        writer.writerow(post)
    elif not posts:
      field_names = ['type', 'target', 'origin', 'created_at']
      writer = csv.DictWriter(csvfile, fieldnames=field_names)
      writer.writeheader()
      for follow in line:
        writer.writerow(follow)
  return render_template('bluesky.html')