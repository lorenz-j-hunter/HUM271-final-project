from time import strftime, gmtime

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

def get_age(created_at: str) -> int:
  """Return the number of months since the date specified in the argument.
  """
  # Separate the date from the string (year-month)
  b: int = created_at.index('T')
  date: list[int] = [int(created_at[0:b].split('-')[0]), int(created_at[0:b].split('-')[1])]
  # get the current date (year-month)
  cur_date: list[int] = [int(strftime('%Y', gmtime())), int(strftime('%m', gmtime()))] 
  # calculate the months in between
  ret = 0
  ret += cur_date[1]
  ret += 12 - date[1]  
  ret += 12 * (cur_date[0] - (date[0] + 1))
  return ret
