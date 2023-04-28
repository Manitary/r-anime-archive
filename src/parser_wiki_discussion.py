"""Parse the discussion wiki and archive the data in the database."""

import re
import pathlib
from dataclasses import dataclass, field
from database import DatabaseDiscussion
from parser_wiki import Parser, Discussion

DISCUSSION_ENTRY_PATH = "src\\queries\\discussion\\add_discussion_entry.sql"
EPISODE_ENTRY_PATH = "src\\queries\\add_episodes.sql"

FILE_PATH = "data\\wiki\\anime\\discussion_archive"

PERMALINK_AND_TEXT = re.compile(r"\[(.*)\]\(.*\/comments\/(\w+)\/.*\)")


class ParserDiscussion(Parser):
    """Parser for episode discussion wiki pages."""

    def parse_file(self) -> None:
        """Parse the contents."""
        if self.year in {2011, 2012, 2013}:
            self.parse_file_1()

    def parse_file_1(self) -> None:
        """Parse the contents.

        Use the formatting for discussion archives years from 2011 to 2013."""
        while not self.out_of_bounds:
            if self.current_line.startswith("* "):
                self.parse_entry()
            else:
                self.next_line()

    def parse_entry(self) -> None:
        """Parse a discussion entry."""
        series_name = self.current_line[1:].strip()
        discussion = Discussion(name=series_name, year=self.year)
        self.next_line()
        while not self.current_line.startswith("* "):
            for title, post_id in PERMALINK_AND_TEXT.findall(self.current_line):
                discussion.episodes[post_id] = title.strip()
            self.next_line()
        if discussion.episodes:
            self.create_entry(discussion=discussion)

    def create_entry(self, discussion: Discussion) -> None:
        """Create a db entry."""
        self._db.begin()
        try:
            with open(DISCUSSION_ENTRY_PATH, encoding="utf8") as f:
                self._db.q.execute(f.read(), discussion.info)
            series_id = self._db.last_row_id
            with open(EPISODE_ENTRY_PATH, encoding="utf8") as f:
                query = f.read()
            for post_id, episode in discussion.episodes.items():
                self._db.q.execute(query, (series_id, post_id, episode))
            self._db.commit()
        except Exception as e:
            print(f"Exception: {e}")
            print(f"{series_id} - {discussion.name} - {post_id} - {episode}")
            self._db.rollback()

    @property
    def year(self) -> int:
        """Return the year included in the file name."""
        file_name = pathlib.Path(self._file_path).stem
        try:
            return int(file_name)
        except ValueError:
            return None
