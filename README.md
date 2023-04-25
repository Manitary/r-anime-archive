# Contents

An unorganised collection of miscellaneous scripts to archive r/anime contents, born from the upcoming 15th May imgur purge.

It can be repurposed for scraping more general Reddit contents.

## scraper_wiki

Download all the wiki pages of a given subreddit, and save them in `.md` format at the given path with a folder structure matching that of the wiki.

## parser_wiki

A class to parse wiki contents. This must be tailored to specific needs, as each wiki will have its own way of formatting contents.

## scraper_comment_tree

Scrape the contents of a given Reddit submission (aka thread or post) and all of its comments.

Save the result as a pickle file, as well as a stripped-down JSON-ified version with selected contents (basically title, body, author, upvote data, creation/edit date, and such). Also has functionality to store relevant metadata in a database (list of submissions/authors, comment tree chain, etc.).

## Other scraper/parser files

These are all versions of the above but suited to each specific class of contents to archive.

## imgur_finder

Originally created to run after wiki_scraper, find all text with the format `[text](imgur link)` in the `.md` files in the given folder (recursively by default), and produce a `.txt` file with the list, grouped by wiki page.
