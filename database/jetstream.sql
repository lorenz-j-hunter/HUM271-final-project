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
  origin text not null,
  created_at text not null
);