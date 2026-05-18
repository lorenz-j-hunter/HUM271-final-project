def encase(target: str) -> str:
  """Encase the target with the character.
  Return TypeError if the character is not a string of
  length 1."""
  return '#' + target + '#' 

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
