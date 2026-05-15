drop table if exists first_dim_for_bluesky;
create table first_dim_for_bluesky (
    "id" integer primary key autoincrement,
    users text not null
);

drop table if exists first_dim_for_x;
create table first_dim_for_x (
    "id" integer primary key autoincrement,
    users text not null
);

drop table if exists first_dim_for_pornhub;
create table first_dim_for_pornhub (
    "id" integer primary key autoincrement,
    title text not null,
    pornstar text not null
);


drop table if exists second_dim_for_bluesky;
create table second_dim_for_bluesky (
    "id" integer primary key autoincrement,
    follows text not null,
    posts text not null
);

drop table if exists second_dim_for_x;
create table second_dim_for_x (
    follows text not null,
    posts text not null,
    item_id text not null
);

drop table if exists second_dim_for_pornhub;
create table second_dim_for_pornhub (
    "id" integer primary key autoincrement,
    tags text not null
);