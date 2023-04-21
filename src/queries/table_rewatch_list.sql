CREATE TABLE IF NOT EXISTS rewatch (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , rewatch_name TEXT NOT NULL
    , sub_name TEXT
    , date_start TEXT
    , date_end TEXT
    , host TEXT
    , processed INTEGER NOT NULL DEFAULT 0
)