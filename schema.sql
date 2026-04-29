drop table if exists bluesky;
create table bluesky (
    id integer primary key autoincrement,
    user text not null,
    gender text not null,
    follows text not null,
    "text" text not null
);

drop table if exists x;
create table x (
    id integer primary key autoincrement,
    user text not null,
    gender text not null,
    follows text not null,
    "text" text not null
);

drop table if exists pornhub;
create table pornhub (
    id integer primary key autoincrement,
    title text not null,
    tag text not null
);