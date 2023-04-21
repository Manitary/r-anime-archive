CREATE TABLE IF NOT EXISTS comment_tree (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , post_id TEXT NOT NULL
    , comment_id TEXT NOT NULL
    , child_id TEXT
    , FOREIGN KEY(post_id) REFERENCES episode(post_id)
)