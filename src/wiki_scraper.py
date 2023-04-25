"""Scrape wiki contents of a subreddit"""

import pathlib
import praw
from praw.models.reddit import subreddit


class WikiScraper:
    """The scraper."""

    def __init__(self, config_name: str) -> None:
        """Initialise a Reddit instance for the given bot name.

        The configuration must be in a .ini file in the workspace folder."""
        self._reddit: praw.Reddit = praw.Reddit(config_name)
        self._subreddit: subreddit.Subreddit = None

    def select_subreddit(self, name: str) -> None:
        """Pick the subreddit to scrape."""
        self._subreddit = self._reddit.subreddit(name)

    def download_wiki_contents(self, path: str = "data\\wiki") -> None:
        """Download all wiki contents of the given subreddit into local files."""
        for wiki_page in self._subreddit.wiki:
            file_path: pathlib.PurePath = pathlib.Path(f"{path}\\{wiki_page}.md")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("w", encoding="utf8") as f:
                print(f"Downloading: {wiki_page}")
                f.write(wiki_page.content_md)


if __name__ == "__main__":
    scraper = WikiScraper("CommentTreeScraper")
    scraper.select_subreddit("anime")
    scraper.download_wiki_contents()
