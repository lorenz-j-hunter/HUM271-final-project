import asyncio, threading, websockets, json
from sqlite3 import dbapi2 as sqlite3

"""Open a Websocket connection for Blyesky with bluesky firehose"""

loop = asyncio.new_event_loop()

def loop_runner():
  asyncio.set_event_loop(loop)
  loop.run_forever()

threading.Thread(target=loop_runner, daemon=True).start()


async def jetstream_stream():
  """Open the stream."""
  url = "wss://jetstream2.us-east.bsky.network/subscribe"

  async with websockets.connect(url) as ws:
    while True:
      msg = await ws.recv()
      try:
        data = json.loads(msg)
      except json.JSONDecodeError:
        continue  # skip malformed messages

      yield data

async def jetstream_worker(db_path, max_events, event_type):
  """Get from the stream."""
  # Here is something that lets you pause until worker is done.
  count = 0
  # Any event that comes through must match the event type.
  if event_type == 'post':
    event_type = 'app.bsky.feed.post'
  elif event_type == 'follow':
    event_type = 'app.bsky.graph.follow'
  # sift through the stream
  async for event in jetstream_stream():
    ret: dict = await parse(event)
    # Only add successful messages. 
    if ret['status'] == 'success':
      db = sqlite3.connect(db_path, check_same_thread=False)
      db.row_factory = sqlite3.Row
      # Add to the database (posts)
      if ret['path'].find(event_type) != -1 and 'app.bsky.feed.post' == event_type:
        db.execute('INSERT INTO posts (author_id, text, created_at) VALUES (?, ?, ?)',
                [ret['author_id'], ret['text'], ret['created_at']])
        db.commit()
        db.close()
        count += 1
      # Add to the database. (follows)
      elif ret['path'].find(event_type) != -1 and 'app.bsky.graph.follow' == event_type:
        db = sqlite3.connect(db_path, check_same_thread=False)
        db.row_factory = sqlite3.Row
        # a person has followed someone
        if ret['op'] == 'create':
          db.execute('INSERT OR IGNORE INTO follows (follower, followee, created_at, rkey) VALUES (?, ?, ?, ?)',
                    [ret['follower'], ret['followee'], ret['created_at'], ret['rkey']])
          # Create their profiles database for later.
          db.execute('''INSERT OR IGNORE INTO profiles
                     (did, display_name, avatar_cid, banner_cid, website, pronouns, created_at, rkey)
                     VALUES (?,?,?,?,?,?,?,?)''',
                     [ret['follower'],'','','','','','',ret['rkey']])
          db.commit()
          db.close()
          count += 1
        # a person has unfollowed. 
        elif ret['op'] == 'delete':
          db.execute('DELETE FROM follows WHERE rkey = (?)',
                           [ret['rkey']])
          db.commit()
          db.close()
    # We stop when we have exceeded the desired limit
    if count >= max_events:
      print("Reached max events, stopping worker")
      db = sqlite3.connect(db_path, check_same_thread=False)
      db.row_factory = sqlite3.Row
      # Tell the system that the worker is done. 
      db.execute('UPDATE worker_done SET value = (?) WHERE value == (?)', ['true', 'false'])
      db.commit()
      db.close()
      break

async def parse(event):
  """Selectively add to the events list"""
  ret: dict = {}
  
  # The message may not be a commit.
  commit = event.get('commit')
  if not commit:
    ret['status'] = 'failure' 
    return ret

  # The message may not have a record.
  # The record is where all of the valuable info is.  
  record = commit.get('record')
  if not record:
    ret['status'] = 'failure' 
    return ret

  ret['status'] = 'success'
  ret['path'] = record.get('$type')

  # We recognize two options in the whole: post and follow.
  if ret['path'].find('app.bsky.feed.post') != -1:
    ret['author_id'] = event.get('did')
    ret['text'] = record.get('text')
    ret['created_at'] = record.get('createdAt')

  elif ret['path'].find('app.bsky.graph.follow') != -1:
    ret['followee'] = record.get('subject')
    ret['follower'] = event.get('did')
    ret['created_at'] = record.get('createdAt')
    ret['op'] = commit.get('operation')
    ret['rkey'] = commit.get('rkey')

  return ret

"""Update"""

async def jetstream_update(db_path, max_events=10000):
  """Look through the stream for any follow deletions or profiles info changes
  which can be used to update the graph."""
  #
  db = sqlite3.connect(db_path, check_same_thread=False)
  db.row_factory = sqlite3.Row
  async for event in jetstream_stream(): 
    count = 0
    ret: dict = await update(event)
    if ret['status'] == 'success':
      if ret['op'] == 'delete':
        # delete a follow
        db.execute('DELETE FROM follows WHERE rkey = (?)', [ret['rkey']])
        db.commit()
        count += 1
      elif ret['op'] == 'update':
        db.execute("UPDATE profiles SET did = (?), display_name = (?), avatar_cid = (?),"
                  "banner_cid = (?), website = (?), pronouns = (?), created_at = (?)"
                  "WHERE rkey = (?)",
                  [ret['did'], ret['display_name'], ret['avatar_cid'], ret['banner_cid'],
                   ret['website'], ret['pronouns'], ret['created_at'], ret['rkey']])
        db.commit()
        count += 1
    if count > max_events:
      print('Reached max events, stopping update.')
      db.close()
      break

async def update(event):
  """Filter events based on whether they can be used to update the 
  graph."""
  ret: dict = {}
  # The message may not be a commit.
  commit = event.get('commit')
  if not commit:
    ret['status'] = 'failure' 
    return ret

  # The message may not have a record.
  # The record is where all of the valuable info is.  
  record = commit.get('record')
  if not record:
    ret['status'] = 'failure' 
    return ret

  ret['status'] = 'success'
  ret['path'] = record.get('$type')

  if commit.get('operation') == 'delete':
    ret['op'] = 'delete'
    ret['rkey'] = commit.get('rkey')
  elif commit.get('operation') == 'update' and commit.get('collection') == 'app.bsky.actor.profile':
    banner = commit.get('banner')
    avatar = record.get('avatar')
    labels = commit.get('labels')
    ret['op'] = 'update'
    ret['rkey'] = commit.get('rkey')

    ret['display_name'] = record.get('displayName')
    ret['did'] = event.get('did')
    # there may not be an avatar or banner.
    if avatar:
      ret['avatar_cid'] = avatar.get('cid')
    else:
      ret['avatar_cid'] = '' 
    if banner:
      ret['banner_cid'] = banner.get('cid') 
    else:
      ret['banner_cid'] = ''
    if record.get('website'):
      ret['website'] = record.get('website')
    else:
      ret['website'] = ''
    if record.get('pronouns'):
      ret['pronouns'] = record.get('pronouns')
    else:
      ret['pronouns'] = ''
    if labels:
      ret['created_at'] = labels.get('createdAt')
    else:
      ret['created_at'] = ''
  else:
    ret['op'] = 'create'
  return ret 