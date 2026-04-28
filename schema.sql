drop table if exists bluesky;
create table bluesky (
    id integer primary key autoincrement,
    user text not null,
    gender text not null,
    follows text not null,
    "text" text not null
)