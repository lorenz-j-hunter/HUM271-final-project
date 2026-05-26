drop table if exists first_dim_for_pornhub;
create table first_dim_for_pornhub (
    item_id integer primary key autoincrement,
    title text not null,
    pornstar text not null,
    views integer not null,
    rating text not null,
    video_id text not null
);

drop table if exists second_dim_for_pornhub;
create table second_dim_for_pornhub (
    tags text not null,
    item_id text not null
);