# Contents

An unorganised collection of miscellaneous scripts to do things with Reddit.

## wiki_scraper

Download all the wiki pages of a given subreddit, and save them in `.md` format at the given path with a folder structure matching that of the wiki.

## imgur_finder

Originally created to run after wiki_scraper, find all text with the format `[text](imgur link)` in the `.md` files in the given folder (recursively by default), and produce a `.txt` file with the list, grouped by wiki page.
