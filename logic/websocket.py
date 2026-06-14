import asyncio, threading, websockets, json
from sqlite3 import dbapi2 as sqlite3
from logic import backfill as rest_update
from logic import jetstream_csv as stream_files

"""Open a Websocket connection for Blyesky with bluesky firehose"""

loop = asyncio.new_event_loop()

def loop_runner():
  asyncio.set_event_loop(loop)
  loop.run_forever()

def backfill(db_path):
  """A wrapper for running a single event on a background loop."""
  asyncio.run_coroutine_threadsafe(rest_update.backfill(db_path), loop)


threading.Thread(target=loop_runner, daemon=True).start()


def get_event_type(parsed: dict[str,str]) -> str:
  if parsed['status'] == 'success':
    if parsed['type'] == 'app.bsky.graph.follow':
      return  'follow'
    elif parsed['type'] == 'app.bsky.feed.post':
      return 'post'
  return 'neither'


async def jetstream_batches(stream, type, batch_size=10, max_events=100_000_000, querystring: str | None='a'):
  batch = []
  print('in batch generator')
  async for event in stream:
    try:
      # yield batch early if disconnect.
      if event['disconnect'] == True:
        batch.insert(0, ['disconnect', event.get('cursor')])
        break
    except KeyError:
      pass
    parsed = await parse(event, params={'querystring': querystring})
    event_type = get_event_type(parsed)
    # filter by event typ
    if type == event_type == 'post' and parsed['status'] == 'success':
      line: list = [
        parsed['author_id'],
        parsed['text'], 
        parsed['created_at']
      ]
      batch.append(line)
    elif type == event_type == 'follow' and parsed['status'] == 'success':
      line: list = [
        parsed['follower'],
        parsed['followee'], 
        parsed['created_at'],
        'false', 
        parsed['rkey']
      ]
      batch.append(line)
    
    # if a batch's size is not batch_size at time of yield, there is a case for that here
    if len(batch) == batch_size:
      yield batch
      batch = []

    if max_events == 0:
      break


  if batch:
    yield batch


async def jetstream_worker(db_path, params={'max_events': '5', 'type': 'post'}):
  """Write the rows from the batch generator"""
  # unpack params
  max_events = params['max_events']
  event_type = params['event_type']
  mark_blocks = params['mark_blocks'] if params['mark_blocks'] == 'yes' else None
  querystring = params['querystring'] if params['querystring'] else None

  conn = sqlite3.connect(db_path, check_same_thread=False)
  conn.row_factory = sqlite3.Row
  conn.execute('BEGIN TRANSACTION;')
  remaining = max_events
  cursor = None
  async for batch in jetstream_batches(jetstream_stream(cursor=cursor), type=event_type, max_events=max_events, querystring=querystring):
    message = batch[0]
    if message[0] == 'disconnect':
      # insert the partially filled batch then reconnect
      cursor = message[1]
      rows = batch[1:]
      break 
    else:
      rows = batch
      cursor = None
    if event_type == 'post':
      conn.executemany(
        'INSERT INTO posts (author_id, text, created_at) VALUES (?, ?, ?)',
        rows 
      )
    else:
      conn.executemany(
        '''INSERT OR IGNORE INTO follows (follower, followee, created_at, blocked, rkey)
                  VALUES (?, ?, ?, ?, ?)''',
        rows
      )
    remaining -= len(rows)
    if remaining <= 0:
      break
  conn.execute('UPDATE worker_done SET value = (?) WHERE value == (?)', ['true', 'false'])
  conn.execute('COMMIT;') 
  print('Completed jetstream worker, stopping')
  stream_files.get_jetstream_csv(db_path=db_path, columns={
    'mark_blocks': mark_blocks 
    })
  conn.close()


async def jetstream_stream(cursor=None):
  url = (
    "wss://jetstream2.us-east.bsky.network/subscribe"
    if not cursor else
    f"wss://jetstream2.us-east.bsky.network/subscribe?cursor={cursor}"
  )
  cursor = None
  try:
    async with websockets.connect(url) as ws:
      while True:
        msg = await ws.recv()
        try:
          data = json.loads(msg)
          cursor = data.get('cursor')
        except json.JSONDecodeError:
          continue  # skip malformed messages

        yield data
  except websockets.exceptions.ConnectionClosed:
    # stream disconnects
    yield {'disconnect': True, 'cursor': cursor}
  except Exception:
    # timeout, network error, etc
    yield {'disconnect': True, 'cursor': cursor}

async def parse(event, params={}) -> dict:
  """Selectively add to the events list"""
  ret: dict = {}
  querystring = params['querystring'] if params['querystring'] else None
  
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
  ret['type'] = record.get('$type')

  # if the desired type is a post.
  if ret['type'].find('app.bsky.feed.post') != -1:
    ret['author_id'] = event.get('did')
    ret['text'] = 'title was none' if not record.get('text') else record.get('text')
    ret['created_at'] = record.get('createdAt')
    if querystring:
      # if querystring is not in title text
      if ret['text'].find(querystring) == -1:
        ret = {}
        ret['status'] = 'failure'
        return ret
  # if the desired type is a follow
  elif ret['type'].find('app.bsky.graph.follow') != -1:
    ret['followee'] = record.get('subject')
    ret['follower'] = event.get('did')
    ret['created_at'] = record.get('createdAt')
    ret['op'] = commit.get('operation')
    ret['rkey'] = commit.get('rkey')

  return ret


"""Update"""


async def jetstream_update(db_path, max_events=10):
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
      # asynchronously backfill the graph
      backfill(db_path)
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

"""End Update"""