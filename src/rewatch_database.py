"""Set up and organise the database for archiving rewatches."""

import os
import sqlite3
import glob
import logging
from logging.handlers import TimedRotatingFileHandler


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    """Change query results from tuple to dict."""
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))


class Database:
    """The database."""

    def __init__(self, database: str) -> None:
        """Initiliase from db path."""
        try:
            self._db = sqlite3.connect(database=database)
            self._db.execute("PRAGMA foreign_keys=ON")
            self._db.row_factory = dict_factory
        except sqlite3.OperationalError:
            logging.error("Failed to open database: %s", database)

    @property
    def q(self) -> sqlite3.Cursor:
        """Access the cursor."""
        return self._db.cursor()

    def setup_tables(self, path: str = "src\\queries") -> None:
        """Create tables."""
        for query in glob.glob(pathname=f"{path}\\table_*.sql"):
            with open(query, encoding="utf8") as f:
                self.q.execute(f.read())
                logging.info("Query executed: %s", query)


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
    db = Database("rewatches.sqlite")
    db.setup_tables()
    logging.info("%s%s", "-" * 60, "\n")
