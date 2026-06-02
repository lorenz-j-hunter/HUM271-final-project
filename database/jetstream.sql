drop table if exists jetstream_post;
create table jetstream_post (
  "id" integer primary key autoincrement,
  "type" text not null,
  "text" text not null,
  created_at text not null 
);

drop table if exists jetstream_follow;
create table jetstream_follow (
  "id" integer primary key autoincrement,
  "type" text not null,
  "target" text not null,
  "origin" text not null,
  created_at text not null
);

drop table if exists follows;
create table follows (
  follower text not null,
  followee text not null,
  PRIMARY KEY (follower, followee),
  created_at text not null
)

--Either `block` or `profile` will be filled. 
drop table if exists jetstream_update;
create table jetstream_update (
  "target" text not null,
  origin text not null,
  "block" text not null, --a user has blocked one of their follows
  "profile" text not null, --a user has updated their profile
  done_at text not null 
);