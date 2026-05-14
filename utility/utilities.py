import os

def get_auth(location: str) -> str:
  """Get an auth token or key from a hidden file."""
  with open(os.path.relpath("authorization/"+location, 'r')) as auth_file:
    ret: str = auth_file.read() 
    return ret
  return None

def encase(char: str, target: str) -> str:
  """Encase the target with the character.
  Return TypeError if the character is not a string of
  length 1."""
  if len(char) != 1:
    raise TypeError(f"In encase(char={char}, target={target}), string is not of length 1.")
  return char + target + char

def extract(target: str) -> dict[str,str]:
  """Return a dict of substrings which are encased
  as defined by the encase() function.
  The dict matches the left of colon with right of colon.
  This operates on a single cell of the database."""
  pre = target.split('#_#')
  ret: dict[str,str] = {}
  for elem in pre:
    elem = elem.strip('#')
    temp = elem.split(':')
    ret[temp[0]] = temp[1]
  return ret
