--Store arguments created by the user for later use.
drop table if exists args;
create table args (
  bluesky_length text not null, 
  querystring text not null,
  max_events text not null,
  "type" text not null,
  mark_blocks text not null
);