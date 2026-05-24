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
  cur = db.execute('SELECT item_id, name, age_months, pronouns FROM first_dim_for_bluesky')
  f = cur.fetchall()
  item_ids: list[int] = [row[0] for row in f]
  names: list[str] = [row[1] for row in f]
  ages: list[int] = [row[2] for row in f]
  pronouns: list[str] = [row[3] for row in f]
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
      'age': [str(ages[item_id-1])], 
      'pronouns': [pronouns[item_id-1]],
      'follows': follows,
      'posts': posts
    }))
  # We write to the file now. 
  with open('../csvfiles/bluesky.csv', 'w', newline='\n') as csvfile:
    field_names = ['name', 'account age', 'pronouns', 'follows', 'posts']
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
            'account age': ages[item_id-1],
            'pronouns': pronouns[item_id-1],
            'follows': follows[i],
            'posts': posts[i]
          })
        for i in range(len(posts), len(follows)):
          writer.writerow({
            'name': names[item_id-1],
            'account age': ages[item_id-1],
            'pronouns': pronouns[item_id-1],
            'follows': follows[i],
            'posts': 'None' 
          })
      # case 2: number of follows < number of posts
      elif len(posts) > len(follows):
        for i in range(len(follows)):
          writer.writerow({
            'name': names[item_id-1],
            'account age': ages[item_id-1],
            'pronouns': pronouns[item_id-1],
            'follows': follows[i],
            'posts': posts[i]
          })
        for i in range(len(follows), len(posts)):
          writer.writerow({
            'name': names[item_id-1],
            'account age': ages[item_id-1],
            'pronouns': pronouns[item_id-1],
            'follows': 'None',
            'posts': posts[i]
          })
      # case 3: number of follows == number of posts
      elif len(posts) == len(follows):
        for i in range(len(follows)):
          writer.writerow({
            'name': names[item_id-1],
            'account age': ages[item_id-1],
            'pronouns': pronouns[item_id-1],
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
  cur = db.execute('SELECT item_id, name, age, affiliation, verified FROM first_dim_for_x') 
  f = cur.fetchall()
  item_ids: list[int] = [row[0] for row in f]
  names: list[str] = [row[1] for row in f]
  ages: list[int] = [row[2] for row in f]
  affiliation: list[str] = [row[3] for row in f]
  verified: list[str] = [row[4] for row in f]
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
      'name': [names[item_id-1]],
      'age': [str(ages[item_id-1])],
      'affiliation': [affiliation[item_id-1]],
      'verified': [verified[item_id-1]],
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
    field_names = ['name', 'did', 'account age', 'affiliation', 'verification status' 'follows', 'posts']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for elem in consolidated:
      # Here, we need to add a for loop. This will loop through the follows/posts.
      # For each follow/post, we write to the file.
      # Case 1: Number of user's follows > number of user's posts.
      if len(elem['follows']) > len(elem['posts']):
        for i in range(len(elem['posts'])):
          writer.writerow({
            'name': elem.get('name', 'None')[0],  
            'did': elem.get('name', 'None')[0], 
            'account age': elem.get('age', 'None')[0],
            'affiliation': elem.get('affiliation', 'None')[0],
            'verification status': elem.get('verified', 'None')[0], 
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
        for i in range(len(elem['posts']), len(elem['follows'])):
          writer.writerow({
            'name': elem.get('name', 'None'), 
            'did': elem.get('name', 'None'), 
            'account age': elem.get('age', 'None')[0],
            'affiliation': elem.get('affiliation', 'None')[0],
            'verification status': elem.get('verified', 'None')[0], 
            'follows': elem['follows'][i],
            'posts': '"None"' 
          })
      # case 2: Number of user's posts > number of user's follows
      elif len(elem['posts']) > len(elem['follows']):
        for i in range(len(elem['follows'])):
          writer.writerow({
            'name': elem.get('name', 'None'), 
            'did': elem.get('name', 'None'), 
            'account age': elem.get('age', 'None')[0],
            'affiliation': elem.get('affiliation', 'None')[0],
            'verification status': elem.get('verified', 'None')[0], 
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
        for i in range(len(elem['posts']), len(elem['follows'])):
          writer.writerow({
            'name': elem.get('name', 'None'), 
            'did': elem.get('name', 'None'), 
            'account age': elem.get('age', 'None')[0],
            'affiliation': elem.get('affiliation', 'None')[0],
            'verification status': elem.get('verified', 'None')[0], 
            'follows': '"None"',
            'posts': elem['posts'][i] 
          })
      # case 3: Number of user's posts == number of user's follows
      else:
        for i in range(len(elem['follows'])):
          writer.writerow({
            'name': elem.get('name', 'None'),
            'did': elem.get('name', 'None'), 
            'account age': elem.get('age', 'None')[0],
            'affiliation': elem.get('affiliation', 'None')[0],
            'verification status': elem.get('verified', 'None')[0], 
            'follows': elem['follows'][i],
            'posts': elem['posts'][i]
          })
  return render_template('x.html')

def get_pornhub_csv(db, max_tags=10):
  """Convert the database file into a csv. 
  The csv represents an undirected and simple graph."""
  # We inserted the video details in the function that precedes this (pornhub())
  # Now, we get them back.
  cur = db.execute("SELECT item_id, title, pornstar, views, rating FROM first_dim_for_pornhub")
  f = cur.fetchall()
  # star_ids is different from item_ids because elements are unique.
  # item_ids (videos) contains elements which correspond to which tags they
  # had. 
  title_ids: list[int] = [row[0] for row in f]
  titles: list[str] = [row[1] for row in f]
  pornstars: list[str] = [row[2] for row in f]
  views: list[int] = [row[3] for row in f]
  ratings: list[str] = [row[4] for row in f]
  # Now we get the second dimension.
  cur = db.execute('SELECT item_id, tags FROM second_dim_for_pornhub')
  f = cur.fetchall()
  video_ids: list[int] = [int(row[0]) for row in f]
  tags: list[str] = [row[1] for row in f]
  # We want to make it so that every video_id is associated with a list
  # of its tags, not like how it was arranged in the database.
  # We now initialize.
  video_to_tags: dict[str, list[str]] = {}
  for video_id in video_ids:
    video_to_tags[str(video_id)] = []
  # We now match.
  for video_id in range(len(video_ids)):
    # Instead of putting the title as the key, its id is the key.
    video_to_tags[str(video_ids[video_id])].append(tags[int(video_id)])
  # consolidated must be initialized first. 
  consolidated: list[dict[str,str]] = []
  for _ in range(max(title_ids)*max_tags): # get at most `max_tags` tags.
    consolidated.append({})
  # for every video ...
  for title_id in title_ids:
    for video_id in video_ids:
      # ... find the star of the video ...
      if title_id == video_id:
        # ... then match the star with the tags of their video. 
        counter = 0 
        while counter < max_tags:
          consolidated[max_tags*(title_id-1) + counter]['title'] = titles[int(title_id)-1]
          consolidated[max_tags*(title_id-1) + counter]['title_id'] = str(title_id)
          consolidated[max_tags*(title_id-1) + counter]['pornstar'] = pornstars[int(video_id-1)].strip('()').strip(',').strip('\'') # a pornstar
          consolidated[max_tags*(title_id-1) + counter]['views'] = str(views[int(title_id)-1])
          consolidated[max_tags*(title_id-1) + counter]['rating'] = ratings[int(title_id)-1]
          # Only insert if there are at least `max_tags`` tags. 
          if video_to_tags[str(title_id)][counter]:
            consolidated[max_tags*(title_id-1) + counter]['tags'] = video_to_tags[str(title_id)][counter] # a tag.
          else:
            consolidated[max_tags*(title_id-1) + counter]['tags'] = 'None'
          counter += 1
  # Now, we open a flat file and insert to it.
  with open('../csvfiles/pornhub.csv', 'w', newline='\n') as csvfile:
    field_names = ['title', 'title_id', 'views', 'rating', 'pornstar', 'tags']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    for row in consolidated:
      writer.writerow(row)
  return render_template('pornhub.html')
