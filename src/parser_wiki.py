"""General wiki parser."""

import re
import abc
from functools import reduce
from operator import ior
from dataclasses import dataclass, field
from database import Database

TABLE_LINK_AND_TEXT = re.compile(r"\[([^\|]*)\]\(\/(?:comments\/)?([^\|]+)\)")
TABLE_LINK = re.compile(r"\[[^\|]*\]\(\/(?:comments\/)?([^\|]+)\)")


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


class Parser(abc.ABC):
    """Parser for wiki pages."""

    def __init__(self, file_path: str, db: Database) -> None:
        self._file_path = file_path
        with open(file_path, encoding="utf-8") as f:
            # Strip \n and ignore empty lines
            self._contents = list(filter(None, (line.rstrip() for line in f)))
        self._idx = 0
        self._db = db

    @abc.abstractmethod
    def parse_file(self) -> None:
        """Parse the contents."""

    @abc.abstractmethod
    def parse_entry(self) -> None:
        """Parse a rewatch entry."""

    def read_table(self) -> list[str]:
        """Parse a markdown table."""
        table = []
        while (not self.out_of_bounds) and self.current_line.count("|") >= 1:
            if not set(self.current_line).issubset({"|", ":", "-"}):
                table.append(self.current_line)
            self.next_line()
        return table

    @staticmethod
    @abc.abstractmethod
    def parse_table(
        table: list[str], rewatch_name: str = None, year: int = None
    ) -> dict:
        """Extract information from the table given in markdown format."""

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

    @abc.abstractmethod
    def create_entry(self) -> None:
        """Create a db entry."""

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

    def next_line(self) -> None:
        """Advance the line counter."""
        self._idx += 1
