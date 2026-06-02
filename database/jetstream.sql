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
  PRIMARY KEY (follower, followee)
);

--Either `block` or `profile` will be filled. 
drop table if exists updates;
create table updates (
  "target" text not null,
  origin text not null,
  "block" text not null, 
  "profile" text not null, 
  done_at text not null 
);