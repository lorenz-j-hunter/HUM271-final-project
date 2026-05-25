drop table if exists jetstream;
create table jetstream (
  "id" integer primary key autoincrement,
  "type" text not null,
  "text" text not null,
  created_at text not null 
);