--This is a static database. 
--The program here does not change it. 
drop table if exists list_of_stars;
create table list_of_stars (
  "id" integer primary key autoincrement,
  star text not null
);