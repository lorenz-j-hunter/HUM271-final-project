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
  cur = db.execute('SELECT item_id, name FROM first_dim_for_bluesky')
  f = cur.fetchall()
  item_ids: list[int] = [row[0] for row in f]
  names: list[str] = [row[1] for row in f]
  # Now, we extract from this. We put each cell in a dict.
  # This is so that the data inside can be used to gather data
  # on the user later.
  for item_id in item_ids:
    # Gather all follows/posts from the user (item_id) in question.
    cur = db.execute('SELECT follows, posts FROM second_dim_for_bluesky WHERE item_id == (?)',
                      [item_id])
    f = cur.fetchall()
    follows: list[str] = [row[0] for row in f]
    posts: list[str] = [row[1] for row in f]
    # `names[item_id]` represents the name of the user in question. Each user has a unique
    # `item_id`, so it is okay to traverse with it.
    consolidated.append(dict({
      'datum': [names[item_id-1]], # account for zero-indexing.
      'follows': follows,
      'posts': posts
    }))
  # We write to the file now. 
  with open('../csvfiles/bluesky.csv', 'w', newline='\n') as csvfile:
    field_names = ['name', 'follows', 'posts']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for item_id in item_ids:
      follows: list[str] = consolidated[item_id-1].get('follows', [])
      posts: list[str] = consolidated[item_id-1].get('posts', [])
      # case 1: number of follows > number of posts
      if len(follows) > len(posts):
        for i in range(len(posts)):
          writer.writerow({
            'name': names[item_id-1],
            'follows': follows[i],
            'posts': posts[i]
          })
        for i in range(len(posts), len(follows)):
          writer.writerow({
            'name': names[item_id-1],
            'follows': follows[i],
            'posts': 'None' 
          })
      # case 2: number of follows < number of posts
      elif len(posts) > len(follows):
        for i in range(len(follows)):
          writer.writerow({
            'name': names[item_id-1],
            'follows': follows[i],
            'posts': posts[i]
          })
        for i in range(len(follows), len(posts)):
          writer.writerow({
            'name': names[item_id-1],
            'follows': 'None',
            'posts': posts[i]

          })
      # case 3: number of follows == number of posts
      elif len(posts) == len(follows):
        for i in range(len(follows)):
          writer.writerow({
            'name': names[item_id-1],
            'follows': follows[i],
            'posts': posts[i]
          })
  return render_template('bluesky.html') 

def get_x_csv(db):
  """Convert the database file into a csv. 
  The csv represents an undirected and simple graph.""" 
  # We first open the first dimension and gather the user data only.
  # Because the other two columns (follows and posts) are two-dimensional,
  # they will be fetched in a different scope.
  consolidated: list[dict[str,list[str]]] = []
  cur = db.execute('SELECT item_id, name FROM first_dim_for_x') 
  f = cur.fetchall()
  item_ids: list[int] = [row[0] for row in f]
  names: list[str] = [row[1] for row in f]
  # Now we do get follows and posts.
  # We want each list of follows and posts to still be associated with the user
  # in question for this data type, so we will append a list do 
  cur = db.execute('SELECT follows, posts FROM second_dim_for_x')
  f = cur.fetchall()
  follows_data: list[str] = []
  posts_data: list[str] = []
  for item_id in item_ids:
    # each user has their own follows/posts.
    follows_data = []
    posts_data = []
    for row in f:
      follow: str = row[0] 
      post: str = row[1]
      db_id: str = row[2]
      # Only in the case that the user is the one we want to get follows, posts from do we
      # fetch them, is what this means. For each user, we loop through the entire second_dim
      # database. Each time, we pick the rows which have the user's item_id on them.
      if db_id == item_id:
        follows_data.append(str(follow))
        posts_data.append(str(post))
    # Now, we add these newly populated lists `follows_data`, etc into the `consolidated`. 
    consolidated.append(dict({
      'datum': [names[item_id-1]],
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
    field_names = ['name', 'did', 'follows', 'posts']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for elem in consolidated:
      # Here, we need to add a for loop. This will loop through the follows/posts.
      # For each follow/post, we write to the file.
      # Case 1: Number of user's follows > number of user's posts.
      if len(elem['follows']) > len(elem['posts']):
        for i in range(len(elem['posts'])):
          writer.writerow({
            'name': elem.get('datum', 'None')[0],  
            'did': elem.get('datum', 'None')[0],  
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
        for i in range(len(elem['posts']), len(elem['follows'])):
          writer.writerow({
            'name': elem.get('datum', 'None'), 
            'did': elem.get('datum', 'None'), 
            'follows': elem['follows'][i],
            'posts': '"None"' 
          })
      # case 2: Number of user's posts > number of user's follows
      elif len(elem['posts']) > len(elem['follows']):
        for i in range(len(elem['follows'])):
          writer.writerow({
            'name': elem.get('datum', 'None'), 
            'did': elem.get('datum', 'None'), 
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
        for i in range(len(elem['posts']), len(elem['follows'])):
          writer.writerow({
            'name': elem.get('datum', 'None'), 
            'did': elem.get('datum', 'None'), 
            'follows': '"None"',
            'posts': elem['posts'][i] 
          })
      # case 3: Number of user's posts == number of user's follows
      else:
        for i in range(len(elem['follows'])):
          writer.writerow({
            'name': elem.get('datum', 'None'),
            'did': elem.get('datum', 'None'), 
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
  # We inserted the video details in the function that precedes this (pornhub())
  # Now, we get them back.
  cur = db.execute("SELECT title, pornstar FROM first_dim_for_pornhub")
  f = cur.fetchall()
  video_data: list[str] = [row[0] for row in f]
  pornstars: list[str] = [row[1] for row in f]
  # So here we make that list. Each element resembles an insertion object
  # being a dict. 
  for i in range(len(video_data)):
    pre: dict[str,str] = extract(video_data[i])
    pre['pornstar'] = pornstars[i].strip('#').strip('()').strip(',').strip('\'')
    consolidated.append(pre)
  # Now, we open a flat file and insert to it. 
  with open('../csvfiles/pornhub.csv', 'w', newline='\n') as csvfile:
    field_names = ['video_id', 'did', 'platform', 'type', 'item_id', 'pornstar']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for row in consolidated:
      writer.writerow(row)
  return render_template('pornhub.html')
