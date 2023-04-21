CREATE TABLE IF NOT EXISTS rewatch (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , anime_name TEXT NOT NULL
    , date_start TEXT
    , date_end TEXT
    , host TEXT
    , processed INTEGER NOT NULL DEFAULT 0
)