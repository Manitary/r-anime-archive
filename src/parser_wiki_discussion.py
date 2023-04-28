"""Parse the discussion wiki and archive the data in the database."""

import re
import pathlib
from operator import ior
from functools import reduce
from string import punctuation
from database import DatabaseDiscussion
from parser_wiki import Parser, Discussion

DISCUSSION_ENTRY_PATH = "src\\queries\\discussion\\add_discussion_entry.sql"
EPISODE_ENTRY_PATH = "src\\queries\\add_episodes.sql"

FILE_PATH = "data\\wiki\\anime\\discussion_archive_edited"

PERMALINK_AND_TEXT = re.compile(
    r"(?:\|([^\|]*)\|\[[^\]]*\]\(https?:\/\/redd\.it\/(\w+)(?:\)|$)"
    r"|\[([^\]]*)\]\([^\s]*comments\/(\w+)[^\)]*(?:\)|$)"
    r"|\[([^\]]*)\]\(\/(\w+)(?:\)|$))"
)
HEADERS = re.compile(r"\|?([^\|]+)\|?")
CONTENTS_LINKS = re.compile(
    r"\[[^\]]+\]\([^|]*(?:comments|redd\.it)?\/(\w+)[^\)]*(?:\)|$)"
)


# Compare with parser_wiki.TableParser to see which one to keep/improve.
class TableDiscussionParser:
    """Parse discussion wiki tables."""

    @staticmethod
    def parse_table_one_header(table: list[str]) -> dict:
        """Parse a table that has a single header row.

        Contents can be in the form:
        - name | [text](link) (| repeat)
        - [name](link) (| repeat)"""
        return reduce(
            ior,
            list(
                {
                    entry[1]: entry[0]
                    for entry in PERMALINK_AND_TEXT.findall(row)
                    if entry[1]
                }
                for row in table[1:]
            ),
        )

    @staticmethod
    def parse_table_alternate_headers(table: list[str]) -> dict:
        """Parse a table that alternate headers and contents.

        Contents have the form:
        - name (| repeat)
          [text](link) (| repeat)"""
        ans = {}
        for pair in zip(table[::2], table[1::2]):
            header_row, link_row = pair
            for title, contents in zip(header_row.split("|"), link_row.split("|")):
                links = CONTENTS_LINKS.findall(contents)
                if links and links[0]:
                    ans[links[0]] = title
        return ans


class ParserDiscussion(Parser):
    """Parser for episode discussion wiki pages."""

    def parse_file(self) -> None:
        """Parse the contents."""
        if self.year in {2011, 2012, 2013, 2014, 2015, 2016}:
            self.parse_file_1(delimiter="* ")
        elif self.year in {2017, 2018, 2019, 2021, 2022}:
            self.parse_file_1(delimiter="**")
        elif self.year in {2020}:
            self.parse_file_1(delimiter="###")

    def parse_file_1(self, delimiter: str) -> None:
        """Parse the contents.

        Use the formatting for discussion archives years from 2011 to 2014."""
        while not self.out_of_bounds:
            if self.current_line.startswith(delimiter):
                self.parse_entry(delimiter=delimiter)
            else:
                self.next_line()

    def parse_entry(self, delimiter: str) -> None:
        """Parse a discussion entry."""
        series_name = self.remove_formatting(self.current_line[2:])
        # print(self.year, series_name)
        discussion = Discussion(name=series_name, year=self.year)
        self.next_line()
        while (not self.out_of_bounds) and (
            not self.current_line.startswith(delimiter)
        ):
            if self.current_line.count("|") >= 1:
                if self.current_line.lstrip(punctuation + " ").startswith("Case"):
                    while self.current_line.count("|") >= 1:
                        for pair in PERMALINK_AND_TEXT.findall(self.current_line):
                            title, post_id = (x for x in pair if x)
                            discussion.episodes[post_id] = title.strip()
                        self.next_line()
                else:
                    if self.current_line.lstrip(punctuation + " ").startswith("Ep."):
                        table_parser = (
                            TableDiscussionParser.parse_table_alternate_headers
                        )
                    else:
                        table_parser = TableDiscussionParser.parse_table_one_header
                    table = self.read_table()
                    discussion.episodes |= table_parser(table)
            else:
                for pair in PERMALINK_AND_TEXT.findall(self.current_line):
                    title, post_id = (x for x in pair if x)
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
                # print(self.year, series_id, discussion.name, post_id, episode)
                self._db.q.execute(
                    query, (series_id, post_id or None, self.remove_formatting(episode))
                )
            self._db.commit()
        except Exception as e:
            print(f"Exception: {e}")
            print(
                f"{self.year} - {series_id} - {discussion.name} - {post_id} - {episode}"
            )
            self._db.rollback()

    @property
    def year(self) -> int:
        """Return the year included in the file name."""
        file_name = pathlib.Path(self._file_path).stem
        try:
            return int(file_name)
        except ValueError:
            return None

    @staticmethod
    def parse_table() -> None:
        pass


if __name__ == "__main__":
    for y in range(2011, 2023):
        print(f"Processing year {y}")
        parser = ParserDiscussion(
            f"{FILE_PATH}\\{y}.md", DatabaseDiscussion(path="data\\discussion.sqlite")
        )
        parser.parse_file()
