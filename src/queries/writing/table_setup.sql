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

CREATE TABLE IF NOT EXISTS imgur_link (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , comment_id TEXT NOT NULL -- submission/comment id
    , is_submission INTEGER NOT NULL DEFAULT 0 -- 0 = comment, 1 = submission
    , imgur_link TEXT NOT NULL
    , processed INTEGER NOT NULL DEFAULT 0 -- 1 = downloaded
    , UNIQUE (comment_id, is_submission, imgur_link) -- only make one entry even if the same link is repeated multiple times in the same post/comment
);
