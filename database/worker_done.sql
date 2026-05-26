drop table if exists worker_done;
create table worker_done (
    "value" text unique  
);

INSERT INTO worker_done ("value") VALUES ("false");