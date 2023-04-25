"""Parse the writing wiki and archive the data in the database."""

import re
from database import DatabaseWriting
from parser_wiki import Parser

WRITING_WIKI = "data\\wiki\\anime\\writing_archive.md"
TABLE_LINK_AND_TEXT = re.compile(r"\[([^\|]*)\]\(\/(?:comments\/)?([^\|]+)\)")
AUTHOR = re.compile(r"\/?u\/([\w_-]+)")

WRITING_ENTRY_PATH = "src\\queries\\writing\\add_writing_entry.sql"


class ParserWriting(Parser):
    """Parser for the writing wiki page."""

    def parse_file(self) -> None:
        """Parse the contents and return a table of entries."""
        table = sorted(
            [
                table_row[1:]
                for row in self._contents
                if row.count("|") >= 1
                and (table_row := [x.strip() for x in row.split("|")])[0].isdigit()
            ]
        )
        with open(WRITING_ENTRY_PATH, encoding="utf8") as f:
            query = f.read()
        for entry in table:
            entry_data = self.parse_entry(entry)
            self.create_entry(data=entry_data, query=query)

    def parse_entry(self, entry: list[str]) -> None:
        """Parse row data."""
        post_date = entry[0]
        title, post_id = TABLE_LINK_AND_TEXT.findall(entry[1])[0]
        if len(entry) == 3:
            if entry[-1] == "Open Discussion":
                author = entry[-1]
            else:
                author = ", ".join(AUTHOR.findall(entry[-1]))
        else:
            # Chihayafuru analysis
            author = "ABoredCompSciStudent, walking_the_way"
        return (post_id, title, post_date, author)

    def parse_table(self) -> None:
        """Not needed here, consider changing the ABC."""

    def create_entry(self, data: tuple[str], query: str) -> None:
        """Insert row data into db."""
        self._db.q.execute(query, data)


if __name__ == "__main__":
    parser = ParserWriting(
        file_path=WRITING_WIKI, db=DatabaseWriting(path="data\\writing.sqlite")
    )
    parser.parse_file()
