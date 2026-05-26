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
  if event_type == 'post':
    event_type = 'app.bsky.feed.post'
  elif event_type == 'follow':
    event_type = 'app.bsky.graph.follow'
  # sift through the stream
  async for event in jetstream_stream():  
    ret: dict[str, dict[str,str]] = await parse(event)
    # Add to the database`
    if ret['status'].get('message', 'None') == 'success':
      if ret['type'].get('message', 'None') == event_type:
        db = sqlite3.connect(db_path, check_same_thread=False)
        db.row_factory = sqlite3.Row
        if event_type == 'app.bsky.feed.post':
          db.execute('INSERT INTO jetstream (type, text, created_at) VALUES (?, ?, ?)',
                    [ret['type'].get('message'),
                    ret['text'].get('message'),
                    ret['created_at'].get('message')])
          db.commit()
        elif event_type == 'app.bsky.graph.follow':
          db.execute('INSERT INTO jetstream (type, text, created_at) VALUES (?, ?, ?)',
                    [ret['type'].get('message'),
                    'n/a',
                    'n/a'])
          db.commit()
        db.close()
        count += 1
    # We stop when we have exceeded the desired limit
    if count >= max_events:
      print("Reached max events, stopping worker")
      db = sqlite3.connect(db_path, check_same_thread=False)
      db.row_factory = sqlite3.Row
      db.execute('UPDATE worker_done SET value = (?) WHERE value == (?)', ['true', 'false'])
      db.commit()
      db.close()
      break

async def parse(event):
  """Selectively add to the events list"""
  ret: dict[str, dict[str,str]] = {}
  
  ret['did'] = {'message': event.get('did')}

  # The message may not be a commit.
  commit = event.get('commit')
  if not commit:
    ret['status'] = {'message': 'None'}
    return ret

  # The message may not have a record.
  # The record is where all of the valuable info is.  
  record = commit.get('record')
  if not record:
    ret['status'] = {'message': 'None'}
    return ret

  ret['status'] = {'message': 'success'}
  ret['type'] = {'message': record.get('$type')}


  if ret['type'].get('message', 'None') == 'post':
    ret['text'] = {'message': record.get('text')}
    ret['created_at'] = {'message': record.get('createdAt')}
  elif ret['type'].get('message', 'None') == 'follow':
    ret['created_at'] = {'message': record.get('createdAt')}

  return ret
