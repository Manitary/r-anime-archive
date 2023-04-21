CREATE TABLE IF NOT EXISTS imgur_link (
    id TEXT NOT NULL PRIMARY KEY UNIQUE
    , new_id TEXT UNIQUE
    , comment_id TEXT
    , FOREIGN KEY(comment_id) REFERENCES comment_link(id)
)