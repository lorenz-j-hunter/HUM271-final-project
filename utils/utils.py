from time import strftime, gmtime

def encase(target: str, char='#') -> str:
  """Encase the target with the character.
  """
  if char == '[]':
    return '[' + target + ']'
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

def tagify(tags: list[str]) -> str:
  """Return a request-friendly format of a list."""
  # Format should be "[\"thing1\", \"thing2"]"
  ret: str = ''
  for tag in tags:
    if tag is not tags[len(tags)-1]: # zero-index
      ret = ret + encase(tag, '\\\"') + ', '
    else:
      ret = ret + encase(tag, '\\\"')
  ret = encase(ret, '[]')
  ret = encase(ret, '"')
  return ret 

def remove(target: str, sub: str) -> str | None:
  """Return a version of `target` which has the first occurence of the
  substring `sub` removed. Return None if sub not in target."""
  if sub not in target:
    return None
  i = 0
  max = len(sub)
  ret = '' # target without `sub`
  j = False
  for char in target: 
    if char == sub[i] and j == False:
      i += 1
    else:
      ret = ret + char
      i = 0 
    if i == max:
      j = True
  return ret
