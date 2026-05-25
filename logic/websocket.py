import asyncio, threading, websockets, json

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

async def jetstream_worker(max_events=50):
  """Get from the stream."""
  count = 0
  async for event in jetstream_stream():  
    await parse(event)
    count += 1
    if count >= max_events:
      print("Reached max events, stopping worker")
      break

events = []
async def parse(event):
  """Selectively add to the events list"""
  ret: dict[str, dict[str,str]] = {}
  
  ret['did'] = event.get('did')

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
  ret['type'] = record.get('$type')

  # We only get posts.
  if ret['type'] == 'app.bsky.feed.post':
    ret['text'] = record.get('text')
    ret['created_at'] = record.get('createdAt')

  events.append(ret)

def get_events():
  """Harvest the data from the jetstream"""
  return events