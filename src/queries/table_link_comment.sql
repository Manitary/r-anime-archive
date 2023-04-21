CREATE TABLE IF NOT EXISTS comment_link (
    id TEXT NOT NULL PRIMARY KEY UNIQUE
    , new_id TEXT UNIQUE
    , FOREIGN KEY(id) REFERENCES tree(comment_id)
)