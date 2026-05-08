# Item is the tool used to retrieve data from the database
# as well as fetch data from it. 
#
# In app.py, instead of appending a string to follows[], users[], etc., let's
# append an item. This makes it possible to retrieve data from the 3D database.
#
# An item has the did, data, and platform all in one. 

empty: dict = {
    'data' : '',
    'did' : '',
    'platform' : '',
    'type' : ''
}
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
        self.id=args['id']
    def __str__(self):
        return self.data + '_' + self.did + '_' + self.platform + '_' + self.type
