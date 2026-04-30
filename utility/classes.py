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

def ret() -> item:
    """Return an empty item."""
    ret: item = item()
    return ret
