from flask import render_template
from sqlite3 import dbapi2 as sqlite3
import csv, os

def get_jetstream_csv(db_path):
  """Populate the csv file for the jetstream"""
  db = sqlite3.connect(db_path, check_same_thread=False)
  db.row_factory = sqlite3.Row
  # First, retrieve the data from the database.
  cur = db.execute('SELECT type, text, created_at FROM jetstream')
  f = cur.fetchall()
  types: list[str] = [row[0] for row in f]
  text: list[str] = [row[1] for row in f]
  created_at: list[str] = [row[2] for row in f]
  posts: list[dict[str,str]] = [] 
  # aggregate into 'posts'
  for i in range(len(types)): # can be any of the columns
    posts.append({
      'type': types[i],
      'text': text[i],
      'created_at': created_at[i]
    })
  # create the csv with aggregated data.
  with open(os.path.relpath('../csvfiles/bsky-jetstream.csv'), 'w', newline='\n') as csvfile:
    field_names = ['type', 'text', 'created_at']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for post in posts:
      writer.writerow(post)
  return render_template('bluesky.html')