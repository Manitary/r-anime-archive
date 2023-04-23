"""Parse the rewatch wiki and archive the data in the database."""

import sys
import re
import pathlib
from functools import reduce
from operator import ior
from dataclasses import dataclass, field
from rewatch_database import Database

# issue with "psi" character
sys.stdout.reconfigure(encoding="utf-8")

REWATCH_ENTRY_PATH = "src\\queries\\add_rewatch_entry.sql"
EPISODE_ENTRY_PATH = "src\\queries\\add_rewatch_episodes.sql"

FILE_PATH = "data\\wiki\\anime\\rewatches\\rewatch_archive\\"

REWATCH = re.compile(r"##[^\#]")
HOSTS = re.compile(r"(\/?u\/[\w_-]+)")
TABLE_LINK_AND_TEXT = re.compile(r"\[([^\|]*)\]\(\/(?:comments\/)?([^\|]+)\)")
TABLE_HEADER = re.compile(r"\[[^\|]+\]\([^\|]+\)")
# LINK_TEXT = re.compile(r"([^\|]+)\|?")
TABLE_LINK = re.compile(r"\[[^\|]*\]\(\/(?:comments\/)?([^\|]+)\)")
REWATCH_YEAR = re.compile(r"(.*) \((\d+)\)")


@dataclass
class Rewatch:
    """A rewatch entry."""

    rewatch_name: str
    rewatch_alt_name: str = None
    table_name: str = None
    hosts: str = None
    year: int = None
    table: list[str] = field(default_factory=list)

    def reset_table(self) -> None:
        """Reset the table properties.

        This is for when a rewatch has multiple sub-entries, e.g. multiple seasons."""
        self.table_name = None
        self.table = None

    @property
    def info(self) -> tuple[str]:
        """Return rewatch info to add to the db."""
        return (
            self.rewatch_name,
            self.rewatch_alt_name,
            self.table_name,
            self.year,
            self.hosts,
        )


class TableParser:
    """Parse a variety of markdown tables used in the rewatch archive."""

    @staticmethod
    def parse_table_no_headers(table: list[str]) -> dict:
        """Parse a table that has no headers."""
        return reduce(
            ior,
            list(
                dict(pair)
                for row in table
                if (pair := TABLE_LINK_AND_TEXT.findall(row))
            ),
        )

    @staticmethod
    def parse_table_alternate_headers(table: list[str]) -> dict:
        """Parse a table that alternates headers and contents."""
        data = {}
        for header, contents in zip(table[::2], table[1::2]):
            titles = list(filter(None, header.split("|")))
            links = [TABLE_LINK.search(field) for field in contents.split("|") if field]
            data.update(dict(zip(titles, [x[1] if x else None for x in links])))
        return data

    @staticmethod
    def parse_table_one_header_alternate_contents(table: list[str]) -> dict:
        """Parse a table that has a single header, and alternating name/link."""
        data = {}
        for row in table[1:]:
            row = list(filter(None, row.split("|")))
            for title, link in zip(row[::2], row[1::2]):
                link = TABLE_LINK.findall(link)
                data[title] = link[0] if link else None
        return data

    @staticmethod
    def parse_table_one_header_contents_right(table: list[str]) -> dict:
        """Parse a table that has a single header, and link in the rightmost column."""
        data = {}
        for row in table[1:]:
            row = list(filter(None, row.split("|")))
            titles, link = row[:-1], row[-1]
            title = " - ".join(title for title in titles)
            link = TABLE_LINK.findall(link)
            data[title] = link[0] if link else None
        return data

    @staticmethod
    def parse_table_one_header_contents_left(table: list[str]) -> dict:
        """Parse a table that has a single header, and link in the leftmost column.

        Used for mod movie series."""
        true_table = [row.split("|")[0] for row in table[1:]]
        return TableParser.parse_table_no_headers(true_table)


class Parser:
    """Parser for rewatch wiki pages."""

    def __init__(self, file_path: str, db: Database) -> None:
        self._file_path = file_path
        with open(file_path, encoding="utf-8") as f:
            # Strip \n and ignore empty lines
            self._contents = list(filter(None, (line.rstrip() for line in f)))
        self._idx = 0
        self._db = db

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

    def read_table(self) -> list[str]:
        """Parse a markdown table."""
        table = []
        while (not self.out_of_bounds) and self.current_line.count("|") >= 1:
            if not set(self.current_line).issubset({"|", ":", "-"}):
                table.append(self.current_line)
            self.next_line()
        return table

    @staticmethod
    def parse_table(
        table: list[str], rewatch_name: str = None, year: int = None
    ) -> dict:
        """Extract information from the table given in markdown format."""
        if (rewatch_name, year) in {
            ("Mod Movie Series", 2022),
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

    @staticmethod
    def remove_formatting(text: str) -> str:
        """Remove bold formatting from markdown code."""
        ans = text.strip()
        while ans.count("*") > 1:
            ans = ans.replace("*", "", 2)
        while ans.startswith("#"):
            ans = ans[1:]
        ans.strip()
        return ans

    def create_entry(self, rewatch: Rewatch) -> None:
        """Create a db entry."""
        try:
            with open(REWATCH_ENTRY_PATH, encoding="utf8") as f:
                self._db.q.execute(f.read(), rewatch.info)
            rewatch_id = self._db.last_row_id
            rewatch_contents = self.parse_table(
                table=rewatch.table, rewatch_name=rewatch.rewatch_name, year=self.year
            )
            with open(EPISODE_ENTRY_PATH, encoding="utf8") as f:
                query = f.read()
                for episode, link in rewatch_contents.items():
                    if link:
                        self._db.q.execute(
                            query,
                            (rewatch_id, link, Parser.remove_formatting(episode)),
                        )
        except BaseException as e:
            print(f"Exception: {e}")
            print(f"{rewatch_id} - {rewatch.rewatch_name} - {episode} - {link}")
        self._db.commit()

    @property
    def current_line(self) -> str:
        """Return the current line being parsed."""
        return self._contents[self._idx]

    @property
    def num_lines(self) -> int:
        """Return the number of total lines of contents."""
        return len(self._contents)

    @property
    def out_of_bounds(self) -> bool:
        """Check if the file is over."""
        return self._idx >= self.num_lines

    @property
    def year(self) -> int:
        """Return the year included in the file name."""
        file_name = pathlib.Path(self._file_path).stem
        try:
            return int(file_name)
        except ValueError:
            return None

    def next_line(self) -> None:
        """Advance the line counter."""
        self._idx += 1


if __name__ == "__main__":
    for y in range(2014, 2023):
        print(f"Processing year {y}")
        parser = Parser(f"{FILE_PATH}{y}.md", Database())
        parser.parse_file()
