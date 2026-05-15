from flask import render_template
from utils.utils import extract
from utils.classes import item
import csv
"""Functions for returning the csv."""

def get_bluesky_csv(db):
  """Convert the database file into a csv. 
  The csv represents an undirected and simple graph."""  
  consolidated: list[dict[str,list[str]]] = []
  # We open the first dimension here. The only column opened is the one
  # with one dimension.
  cur = db.execute('SELECT users FROM first_dim_for_bluesky')
  f = cur.fetchall()
  user_data: list[str] = [row[0] for row in f]
  # Now, we extract from this. We put each cell in a dict.
  # This is so that the data inside can be used to gather data
  # on the user later.
  for item_id in range(len(user_data)):
    cur = db.execute('SELECT follows, posts FROM second_dim_for_bluesky WHERE id == (?)',
                      [item_id])
    f = cur.fetchall()
    follows: list[str] = [row[0] for row in f]
    posts: list[str] = [row[1] for row in f]
    consolidated.append(dict({
      'datum': [str(item(extract(user_data[item_id])))],
      'follows': follows,
      'posts': posts
    }))
  # We write to the file now.
  # The mapping is surjective if the codomain is 'users' and domain is 'follows/posts', so
  # we loop by user and then insert all of their follows or posts. 
  with open('../csvfiles/bluesky.csv', 'w', newline='\n') as csvfile:
    field_names = ['user', 'follows', 'posts']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for item_id in range(len(user_data)):
      follows: list[str] = consolidated[item_id].get('follows', [])
      posts: list[str] = consolidated[item_id].get('posts', [])
      # case 1: number of follows > number of posts
      if len(follows) > len(posts):
        for i in range(len(posts)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': follows[i].split('#_#')[0].strip('#'),
            'posts': posts[i].split('#_#')[0].strip('#')
          })
        for i in range(len(posts), len(follows)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': follows[i].split('#_#')[0].strip('#'),
            'posts': 'None' 
          })
      # case 2: number of follows < number of posts
      elif len(posts) > len(follows):
        for i in range(len(follows)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': follows[i].split('#_#')[0].strip('#'),
            'posts': posts[i].split('#_#')[0].strip('#')
          })
        for i in range(len(follows), len(posts)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': 'None',
            'posts': posts[i].split('#_#')[0].strip('#')

          })
      # case 3: number of follows == number of posts
      elif len(posts) == len(follows):
        for i in range(len(follows)):
          writer.writerow({
            'user': user_data[item_id].split('#_#')[0].strip('#'),
            'follows': follows[i].split('#_#')[0].strip('#'),
            'posts': posts[i].split('#_#')[0].strip('#')
          })
  return render_template('bluesky.html') 

def get_x_csv(db):
  """Convert the database file into a csv. 
  The csv represents an undirected and simple graph.""" 
  # We first open the first dimension and gather the user data only.
  # Because the other two columns (follows and posts) are two-dimensional,
  # they will be fetched in a different scope.
  consolidated: list[dict[str,list[str]]] = []
  cur = db.execute('SELECT users FROM first_dim_for_x') 
  f = cur.fetchall()
  user_data: list[str] = [row[0] for row in f]
  # Now we do get follows and posts.
  # We want each list of follows and posts to still be associated with the user
  # in question for this data type, so we will append a list do 
  cur = db.execute('SELECT follows, posts FROM second_dim_for_x')
  f = cur.fetchall()
  follows_data: list[str] = []
  posts_data: list[str] = []
  for datum in user_data:
    user_item_id: str = datum.split('#_#')[4].strip('#')
    for row in f:
      follow: item = item(extract(row[0])) #keyError here
      post: str = row[1]
      # Only in the case that the user is the one we want to get follows, posts from do we
      # fetch them, is what this means. For each user, we loop through the entire second_dim
      # database. Each time, we pick the rows which have the user's item_id on them.
      if follow.get('item_id') == user_item_id:
        follows_data.append(str(follow))
        posts_data.append(str(post))
    # Now, we add these newly populated lists `follows_data`, etc into the `consolidated`. 
    consolidated.append(dict({
      'datum': [str(item(extract(datum)))],
      'follows': follows_data,
      'posts': posts_data
    }))
  # Now it comes down to making a csv out of this extracted and consolidated data.
  # For each user, we list all follows and posts. 
  # This is a surjective operation, and most of the rows for column 'users' will be copies.
  # If there are more posts than follows, the `follows` column will have row 'None' once
  # all of the follows have been printed. Likewise if there are more follows than posts. 
  # Now, we open a flat file and insert to it. 
  with open('../csvfiles/x.csv', 'w', newline='\n') as csvfile:
    field_names = ['user', 'did', 'follows', 'posts']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for elem in consolidated:
      # Here, we need to add a for loop. This will loop through the follows/posts.
      # For each follow/post, we write to the file.
      # Case 1: Number of user's follows > number of user's posts.
      if len(elem['follows']) > len(elem['posts']):
        for i in range(len(elem['posts'])):
          writer.writerow({
            'user': elem.get('datum')[0].split('#_#')[0].strip('#'),  # type: ignore
            'did': elem.get('datum')[0].split('#_#')[1].strip('#'),  # pyright: ignore[reportOptionalSubscript]
            'follows': elem['follows'][i].split('#_#')[0].strip('#'),
            'posts': elem['posts'][i].split('#_#')[0].strip('#')
          })
        for i in range(len(elem['posts']), len(elem['follows'])):
          writer.writerow({
            'user': elem.get('datum').split('#_#')[0].strip('#'), # type: ignore
            'did': elem.get('datum').split('#_#')[1].strip('#'), # type: ignore
            'follows': elem['follows'][i],
            'posts': '"None"' 
          })
      # case 2: Number of user's posts > number of user's follows
      elif len(elem['posts']) > len(elem['follows']):
        for i in range(len(elem['follows'])):
          writer.writerow({
            'user': elem.get('datum').split('#_#')[0].strip('#'), # type: ignore
            'did': elem.get('datum').split('#_#')[1].strip('#'), # type: ignore
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
        for i in range(len(elem['posts']), len(elem['follows'])):
          writer.writerow({
            'user': elem.get('datum').split('#_#')[0].strip('#'), # type: ignore
            'did': elem.get('datum').split('#_#')[1].strip('#'), # type: ignore
            'follows': '"None"',
            'posts': elem['posts'][i] 
          })
      # case 3: Number of user's posts == number of user's follows
      else:
        for i in range(len(elem['follows'])):
          writer.writerow({
            'user': elem.get('datum').split('#_#')[0].strip('#'), # type: ignore
            'did': elem.get('datum').split('#_#')[1].strip('#'), # type: ignore
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
  return render_template('x.html')

def get_pornhub_csv(db):
  """Convert the database file into a csv. 
  The csv represents an undirected and simple graph."""
  # First, we open the database.
  # We are gathering a source and target for each row.
  # We gather a list; each element represents a single cell of the column
  # in question.
  consolidated: list[dict[str,str]] = []
  # We first get the video details...
  cur = db.execute("SELECT title, pornstar FROM first_dim_for_pornhub")
  f = cur.fetchall()
  video_data: list[str] = [row[0] for row in f]
  pornstar: list[str] = [row[1] for row in f]
  # So here we make that list. Each element resembles an insertion object
  # being a dict. 
  for i in range(len(video_data)):
    pre: dict[str,str] = extract(video_data[i])
    pre['pornstar'] = pornstar[i]  
    consolidated.append(pre)
  # Now, we open a flat file and insert to it. 
  with open('../csvfiles/pornhub.csv', 'w', newline='\n') as csvfile:
    field_names = ['video_id', 'did', 'platform', 'type', 'item_id', 'pornstar']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for row in consolidated:
      writer.writerow(row)
  return render_template('pornhub.html')
