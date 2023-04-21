CREATE TABLE IF NOT EXISTS episode (
    id INTEGER NOT NULL
    , post_id TEXT NOT NULL
    , title TEXT
    , FOREIGN KEY(id) REFERENCES rewatch(id)
    , PRIMARY KEY(id, post_id)
)