CREATE TABLE IF NOT EXISTS comment_tree (
    comment_id TEXT NOT NULL PRIMARY KEY UNIQUE
    , post_id TEXT NOT NULL
    , parent_id TEXT
    , FOREIGN KEY(post_id) REFERENCES episode(post_id) ON DELETE RESTRICT ON UPDATE CASCADE
)