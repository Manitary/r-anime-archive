CREATE TABLE IF NOT EXISTS rewatch (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , rewatch_name TEXT NOT NULL -- name of the rewatch series
    , alt_name TEXT -- usually reserved to eng/jp alternate name
    , sub_name TEXT -- optional for further division (e.g. seasons)
    , rewatch_year INT
    , hosts TEXT
    , processed INTEGER NOT NULL DEFAULT 0 -- 1 if all the posts related to the rewatch had their comment tree scraped
    , UNIQUE(rewatch_name, alt_name, sub_name, hosts, rewatch_year)
);

CREATE TABLE IF NOT EXISTS episode (
    id INTEGER NOT NULL
    , post_id TEXT NOT NULL PRIMARY KEY UNIQUE
    , title TEXT -- post title
    , FOREIGN KEY(id) REFERENCES rewatch(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS comment_tree (
    comment_id TEXT NOT NULL PRIMARY KEY UNIQUE
    , post_id TEXT NOT NULL
    , parent_id TEXT -- None for top level comments
    , FOREIGN KEY(post_id) REFERENCES episode(post_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS imgur_link (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , comment_id TEXT NOT NULL -- submission/comment id
    , is_submission INTEGER NOT NULL DEFAULT 0 -- 0 = comment, 1 = submission
    , imgur_link TEXT NOT NULL
    , processed INTEGER NOT NULL DEFAULT 0 -- 1 = downloaded
    , UNIQUE (comment_id, is_submission, imgur_link) -- only make one entry even if the same link is repeated multiple times in the same post/comment
);
