drop table if exists posts;
create table posts (
  author_id text not null,
  "text" text not null,
  created_at text not null 
);

drop table if exists follows;
create table follows (
  follower text not null,
  followee text not null,
  created_at text not null,
  rkey text not null, -- used for edge deletion
  blocked text not null
  PRIMARY KEY (follower, followee)
);

--Either `block` or `profile` will be filled. 
drop table if exists profiles;
create table profiles (
  did text not null,
  display_name text not null,
  avatar_cid text not null,
  banner_cid text not null,
  website text not null,
  pronouns text not null,
  created_at text not null,
  rkey text not null,
  PRIMARY KEY (did, display_name) 
);