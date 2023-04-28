"""Database setup."""

import os
import sqlite3
import abc
import logging
from logging.handlers import TimedRotatingFileHandler

REWATCH_PATH = "src\\queries\\rewatch"
WRITING_PATH = "src\\queries\\writing"
DISCUSSION_PATH = "src\\queries\\discussion"
TABLE_QUERY = "table_setup.sql"


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    """Change query results from tuple to dict."""
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))


class Database(abc.ABC):
    """The database."""

    def __init__(self, path: str) -> None:
        """Initiliase from db path."""
        try:
            self._db = sqlite3.connect(database=path)
            self._db.execute("PRAGMA foreign_keys = ON")
            self._db.row_factory = dict_factory
            self._db.isolation_level = None
        except sqlite3.OperationalError:
            logging.error("Failed to open database: %s", path)

    @property
    def q(self) -> sqlite3.Cursor:
        """Access the cursor."""
        return self._db.cursor()

    @abc.abstractmethod
    def setup_tables(self) -> None:
        """Create tables."""

    @property
    def last_row_id(self) -> int:
        """Return the last inserted row id.

        Used to get the latest autoincremented id after insertion."""
        return self.q.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    def begin(self) -> None:
        """Begin transaction."""
        self.q.execute("BEGIN")

    def commit(self) -> None:
        """Commit transactions."""
        self._db.commit()

    def rollback(self) -> None:
        """Rollback transaction."""
        self._db.rollback()


class DatabaseRewatch(Database):
    """Rewatch database."""

    def setup_tables(self) -> None:
        """Create tables."""
        with open(f"{REWATCH_PATH}\\{TABLE_QUERY}", encoding="utf8") as f:
            query = f.read()
        self.q.executescript(query)
        logging.info("Query executed: %s", f"{REWATCH_PATH}\\{TABLE_QUERY}")


class DatabaseWriting(Database):
    """Writing database."""

    def setup_tables(self) -> None:
        """Create tables."""
        with open(f"{WRITING_PATH}\\{TABLE_QUERY}", encoding="utf8") as f:
            query = f.read()
        self.q.executescript(query)
        logging.info("Query executed: %s", f"{WRITING_PATH}\\{TABLE_QUERY}")


class DatabaseDiscussion(Database):
    """Discussion database."""

    def setup_tables(self) -> None:
        with open(f"{DISCUSSION_PATH}\\{TABLE_QUERY}", encoding="utf8") as f:
            query = f.read()
        self.q.executescript(query)
        logging.info("Query executed: %s", f"{DISCUSSION_PATH}\\{TABLE_QUERY}")


def create_database(db: Database) -> None:
    """Create db and set up tables."""
    db.setup_tables()


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        handlers=[
            TimedRotatingFileHandler(
                filename="logs\\db.log", when="midnight", backupCount=7, encoding="utf8"
            )
        ],
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )
    logging.info("-" * 60)
    create_database(db=DatabaseRewatch(path="data\\rewatches.sqlite"))
    create_database(db=DatabaseWriting(path="data\\writing.sqlite"))
    create_database(db=DatabaseDiscussion(path="data\\discussion.sqlite"))
    logging.info("%s%s", "-" * 60, "\n")
