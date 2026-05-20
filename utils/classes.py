import requests

# Item is the tool used to retrieve data from the database
# as well as fetch data from it. 
#
# In app.py, instead of appending a string to follows[], users[], etc., let's
# append an item. This makes it possible to retrieve data from the 3D database.
#
# An item has the did, data, and platform all in one. 

class item:
  data: str = ''
  did: str = ''
  platform: str = ''
  type: str = ''
  item_id: str = '' 
  def __init__(self, args: dict):
      self.data=args['data']
      self.did=args['did']
      self.platform=args['platform']
      self.type=args['type']
      self.item_id=args['item_id']
  def __repr__(self):
      return self.data + '_' + self.did + '_' + self.platform + '_' + self.type + '_' + self.item_id
  def get(self, item: str) -> str | None:
    """A `get` method for this class."""
    if item == 'data':
      return self.data
    elif item == 'did':
      return self.did
    elif item == 'platform':
      return self.platform
    elif item == 'type':
      return self.type
    elif item == 'item_id':
      return self.item_id
    else:
      return None

# Pair a response with other things.
class compound:
  response: requests.Response
  comment: str = ''
  def __init__(self, args: dict):
    if not args['response'] or not args['comment']:
      raise TypeError('Class \'compound\' not initialized with all data')
    if type(args['response']) is not requests.Response:
      raise TypeError('\'response\' not initialized with type \'requests.Response\'')
    if type(args['comment']) is not str:
      raise TypeError('\'comment\' not initialized with type \'str\'')
    self.response = args['response']
    self.comment = args['comment']
  def get(self, arg: str) -> str | requests.Response | None:
    """Getter method for this class"""
    if arg == 'response':
      return self.response
    elif arg == 'comment':
      return self.comment
    else:
      raise TypeError(f'\'{arg}\' not an attribute of \'compound\'')