CREATE TABLE IF NOT EXISTS writing (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , post_id TEXT NOT NULL UNIQUE
    , title TEXT NOT NULL
    , post_date TEXT
    , author TEXT
    , processed INTEGER NOT NULL DEFAULT 0 -- 1 if the comment tree was scraped
);

CREATE TABLE IF NOT EXISTS comment_tree (
    comment_id TEXT NOT NULL PRIMARY KEY UNIQUE
    , post_id TEXT NOT NULL
    , parent_id TEXT -- None for top level comments
    , FOREIGN KEY(post_id) REFERENCES writing(post_id) ON DELETE RESTRICT ON UPDATE CASCADE
);
