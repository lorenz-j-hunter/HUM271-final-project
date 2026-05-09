import string, random, os

def get_auth(location: str) -> str:
  """Get an auth token or key from a hidden file."""
  with open(os.path.relpath("authorization/"+location, 'r')) as auth_file:
    ret: str = auth_file.read() 
    return ret
  return None

def make_token():
    """A token maker for the Pornhub API only.
    Made by Copilot 2026."""
    alphabet = string.digits + string.ascii_lowercase
    return ''.join(random.choice(alphabet) for _ in range(15))

def encase(char: str, target: str) -> str:
  """Encase the target with the character.
  Return TypeError if the character is not a string of
  length 1."""
  if len(char) is not 1:
    raise TypeError(f"In encase(char={char}, target={target}), string is not of length 1.")
  return char + target + char

def extract(target: str) -> list[str]:
  """Return a list of substrings which are encased
  as defined by the encase() function."""
  pre = target.split('"_"')
  for elem in pre:
    elem.strip('"')
  return pre
