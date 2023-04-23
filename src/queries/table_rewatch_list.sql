CREATE TABLE IF NOT EXISTS rewatch (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE
    , rewatch_name TEXT NOT NULL -- name of the rewatch series
    , alt_name TEXT -- usually reserved to eng/jp alternate name
    , sub_name TEXT -- optional for further division (e.g. seasons)
    , rewatch_year INT
    , hosts TEXT
    , processed INTEGER NOT NULL DEFAULT 0
    , UNIQUE(rewatch_name, alt_name, sub_name, hosts, rewatch_year)
)