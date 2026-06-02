from flask import render_template
from sqlite3 import dbapi2 as sqlite3
import csv, os

def get_jetstream_csv(db_path):
  """Populate the csv file for the jetstream"""
  db = sqlite3.connect(db_path, check_same_thread=False)
  db.row_factory = sqlite3.Row
  # Determine if its follow or post
  cur = db.execute('SELECT author_id FROM posts')
  f = cur.fetchone()[0]
  isfull: bool = len(f) > 1
  #
  line: list[dict[str,str]] = []
  # i.e. if 'posts' was selected  
  if isfull:
    # First, retrieve the data from the database.
    cur = db.execute('SELECT author_id, text, created_at FROM posts')
    f = cur.fetchall()
    author_ids: list[str] = [row[0] for row in f]
    text: list[str] = [row[1] for row in f]
    created_at: list[str] = [row[2] for row in f]
    # aggregate into 'posts'
    for i in range(len(author_ids)): # can be any of the columns
      line.append(dict({
        'author_id': author_ids[i],
        'text': text[i],
        'created_at': created_at[i]
      }))
  # i.e. if 'follow' was selected
  elif not isfull:
    # First, retrieve the data from the database.
    cur = db.execute('SELECT follower, followee, created_at FROM follows')
    f = cur.fetchall()
    followee: list[str] = [row[1] for row in f]
    follower: list[str] = [row[2] for row in f]
    created_at: list[str] = [row[3] for row in f]
    # aggregate into 'posts'
    for i in range(len(follower)): # can be any of the columns
      line.append(dict({
        'author_id': follower[i],
        'followee': followee[i],
        'follower': follower[i],
        'created_at': created_at[i]
      }))
  # create the csv with aggregated data.
  with open(os.path.relpath('../csvfiles/bsky-jetstream.csv'), 'w', newline='\n') as csvfile:
    if isfull: 
      field_names = ['author_id', 'text', 'created_at']
      writer = csv.DictWriter(csvfile, fieldnames=field_names)
      writer.writeheader()
      for post in line:
        writer.writerow(post)
    elif not isfull:
      field_names = ['author_id', 'followee', 'follower', 'created_at']
      writer = csv.DictWriter(csvfile, fieldnames=field_names)
      writer.writeheader()
      for follow in line:
        writer.writerow(follow)
  return render_template('bluesky.html')