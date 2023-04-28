CREATE TABLE IF NOT EXISTS discussion (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , series_name TEXT NOT NULL -- name of the series
    , series_year INT
    , notes TEXT
    , processed INTEGER NOT NULL DEFAULT 0 -- 1 if all the posts related to the series had their comment tree scraped
    , UNIQUE(series_name)
);

CREATE TABLE IF NOT EXISTS episode (
    id INTEGER NOT NULL
    , post_id TEXT NOT NULL PRIMARY KEY UNIQUE
    , title TEXT -- post title
    , FOREIGN KEY(id) REFERENCES discussion(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS comment_tree (
    comment_id TEXT NOT NULL PRIMARY KEY UNIQUE
    , post_id TEXT NOT NULL
    , parent_id TEXT -- None for top level comments
    , FOREIGN KEY(post_id) REFERENCES discussion(post_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS imgur_link (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , comment_id TEXT NOT NULL -- submission/comment id
    , is_submission INTEGER NOT NULL DEFAULT 0 -- 0 = comment, 1 = submission
    , imgur_link TEXT NOT NULL
    , processed INTEGER NOT NULL DEFAULT 0 -- 1 = downloaded
    , error404 INTEGER NOT NULL DEFAULT 0 -- 1 = the link returns 404, prevent future attempts of scraping
    , UNIQUE (comment_id, is_submission, imgur_link) -- only make one entry even if the same link is repeated multiple times in the same post/comment
);
