drop table if exists first_dim_for_x;
create table first_dim_for_x (
    item_id integer primary key autoincrement,
    "name" text not null,
    did text not null,
    age integer not null,
    affiliation text not null,
    verified text not null
);

drop table if exists second_dim_for_x;
create table second_dim_for_x (
    follows text not null,
    posts text not null,
    item_id text not null
);