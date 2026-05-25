from flask import render_template
import csv

def get_jetstream_csv(posts):
  # Now, we open a flat file and insert to it.
  with open('../csvfiles/bsky_jetstream.csv', 'w', newline='\n') as csvfile:
    field_names = ['type', 'text', 'created_at']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for post in posts:
      if post['status'].get('message', 'None') is 'success':
        if post['type'] is 'app.bsky.feed.post':
          writer.writerow(post)
  return render_template('bluesky.html')