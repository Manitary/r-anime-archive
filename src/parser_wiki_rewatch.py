"""Parse the rewatch wiki and archive the data in the database."""

import re
import pathlib
from database import DatabaseRewatch
from parser_wiki import TableParser, Rewatch, Parser

REWATCH_ENTRY_PATH = "src\\queries\\rewatch\\add_rewatch_entry.sql"
EPISODE_ENTRY_PATH = "src\\queries\\add_episodes.sql"

FILE_PATH = "data\\wiki\\anime\\rewatches\\rewatch_archive_edited\\"

REWATCH = re.compile(r"##[^\#]")
HOSTS = re.compile(r"(\/?u\/[\w_-]+)")
TABLE_LINK_AND_TEXT = re.compile(r"\[([^\|]*)\]\(\/(?:comments\/)?([^\|]+)\)")
TABLE_HEADER = re.compile(r"\[[^\|]+\]\([^\|]+\)")
REWATCH_YEAR = re.compile(r"(.*) \((\d+)\)")


class ParserRewatch(Parser):
    """Parser for rewatch wiki pages."""

    def parse_file(self) -> None:
        """Parse the contents."""
        while self._idx < self.num_lines:
            if REWATCH.match(self.current_line):
                self.parse_entry()
            else:
                self.next_line()

    def parse_entry(self) -> None:
        """Parse a rewatch entry."""
        rewatch_name = self.remove_formatting(self.current_line[2:])
        year = self.year
        if self.year == 2014:
            rewatch_name, year = REWATCH_YEAR.findall(rewatch_name)[0]
        rewatch = Rewatch(rewatch_name=rewatch_name, year=year)
        self.next_line()
        while not self.out_of_bounds:
            if REWATCH.match(self.current_line):
                break
            if self.current_line.startswith("Host"):
                rewatch.hosts = ", ".join(HOSTS.findall(self.current_line))
                self.next_line()
            elif self.current_line.count("|") >= 1:
                rewatch.table = self.read_table()
            elif self.current_line.startswith("*") or self.current_line.startswith(
                "###"
            ):
                if rewatch.hosts:
                    rewatch.table_name = self.remove_formatting(self.current_line)
                else:
                    rewatch.rewatch_alt_name = self.remove_formatting(self.current_line)
                self.next_line()
            else:
                self.next_line()
            if rewatch.table:
                if rewatch.table[0].split("|")[1] == "**Host**":
                    rewatch.hosts = ", ".join(
                        row.split("|")[1].strip() for row in rewatch.table[1:]
                    )
                self.create_entry(rewatch=rewatch)
                rewatch.reset_table()

    @staticmethod
    def parse_table(
        table: list[str], rewatch_name: str = None, year: int = None
    ) -> dict:
        """Extract information from the table given in markdown format."""
        if (rewatch_name, year) in {
            ("Mod Movie Series", 2022),
            ("Summer Movie Series", 2022),
        }:
            return TableParser.parse_table_one_header_contents_left(table)
        if (rewatch_name, year) in {
            ("Ah! My Goddess", 2016),
            ("Baka to Test", 2016),
            ("Barakamon", 2016),
            ("Aria", 2015),
            ("Amagami SS", 2015),
            ("Kara no Kyoukai", 2015),
        }:
            return TableParser.parse_table_one_header_alternate_contents(table)
        if (rewatch_name, year) in {
            ("Anime Movie Fortnight", 2015),
            ("Halloween Horror Week", 2015),
            ("Shinseiki Evangelion (Rebuild)", 2016),
        }:
            return TableParser.parse_table_one_header_contents_right(table)
        if TABLE_LINK_AND_TEXT.findall(table[0]):
            return TableParser.parse_table_no_headers(table)
        if not TABLE_HEADER.findall(table[0]):
            return TableParser.parse_table_alternate_headers(table)
        raise ValueError("Invalid table format.")

    @property
    def year(self) -> int:
        """Return the year included in the file name."""
        file_name = pathlib.Path(self._file_path).stem
        try:
            return int(file_name)
        except ValueError:
            return None


if __name__ == "__main__":
    for y in range(2014, 2023):
        print(f"Processing year {y}")
        parser = ParserRewatch(
            f"{FILE_PATH}{y}.md", DatabaseRewatch(path="data\\rewatches.sqlite")
        )
        parser.parse_file()
