import requests

# This is raised if the user enters data which causes some sort of semantic error.
#
# The fieldError is used because regex patterns cannot catch all
# errors a user might cause.
class FieldError(Exception):
  def __init__(self, message, url=None, status=None):
    super().__init__(message)
    self.url = url
    self.status = status

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