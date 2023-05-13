"""Archive/Wayback machine module."""

import os
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
import wayback
import database

logger = logging.getLogger(__name__)

IMGUR_TIME = datetime.datetime(year=2023, month=4, day=19)


def is_archived(
    client: wayback.WaybackClient, time: datetime.datetime, url: str
) -> None:
    """Verify whether the url was archived at or after the given time."""
    results = client.search(url, from_date=time)
    try:
        record = next(results)
    except StopIteration:
        return False
    if record:
        print(f"Url {url} archived with timestamp {record.timestamp}")
        logger.info("Url %s archived with timestamp %s", url, record.timestamp)
    return True


def main(db: database.Database, time: datetime.datetime) -> None:
    """Do the thing."""
    client = wayback.WaybackClient()
    entries = db.q.execute(
        "SELECT DISTINCT imgur_link FROM imgur_link WHERE archived = 0"
    ).fetchall()
    for entry in entries:
        url = entry["imgur_link"]
        print(f"Checking url: {url}")
        logging.info("Checking url: %s", url)
        status = 1 if is_archived(client, time, url) else 2
        print(f"Status: {'found' if status==1 else 'not found'}")
        logging.info("Status of url %s: %s", url, status)
        db.q.execute(
            "UPDATE imgur_link SET archived = ? WHERE imgur_link = ?", (status, url)
        )
        logging.info("db entry for url %s updated", url)


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        handlers=[
            TimedRotatingFileHandler(
                filename="logs\\archive.log",
                when="midnight",
                backupCount=7,
                encoding="utf8",
            )
        ],
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )
    logging.info("-" * 60)
    main(
        db=database.DatabaseWriting("data\\rewatches.sqlite"),
        time=IMGUR_TIME,
    )
    logging.info("%s%s", "-" * 60, "\n")
