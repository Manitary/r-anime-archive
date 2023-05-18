"""Archive/Wayback machine module."""

import os
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
import sqlite3
import ratelimit
import wayback
import waybackpy
import database

logger = logging.getLogger(__name__)

IMGUR_TIME = datetime.datetime(year=2023, month=4, day=19)


def is_archived(client: wayback.WaybackClient, url: str) -> bool:
    """Verify whether the url was archived at or after the given time."""
    results = client.search(url, limit=-1, fast_latest=True)
    try:
        record = next(results)
    except StopIteration:
        return False
    if record:
        print(f"Url {url} archived with timestamp {record.timestamp}")
        logger.info("Url %s archived with timestamp %s", url, record.timestamp)
    return record.timestamp


def is_archived_new(url: str) -> bool:
    """The same but with waybackpy."""
    availability_api = waybackpy.WaybackMachineAvailabilityAPI(url)
    availability_api.newest()
    if availability_api.json is None:
        return None
    return availability_api.timestamp()


def check_archive_status(db: database.Database) -> bool:
    """Given a table of URLs, check whether they have been archived any time from the given date."""
    client = wayback.WaybackClient()
    entries = db.q.execute("SELECT DISTINCT url FROM urls WHERE checked = 0").fetchall()
    for entry in entries:
        url = entry["url"]
        print(f"Checking url: {url}")
        logging.info("Checking url: %s", url)
        timestamp = is_archived(client, url)
        status = 1 if timestamp else 0
        print(f"Status: {'found' if status==1 else 'not found'}")
        logging.info("Status of url %s: %s", url, status)
        while True:
            try:
                db.q.execute(
                    "UPDATE urls SET checked = 1, archived = ?, archived_time = ? WHERE url = ?",
                    (status, timestamp, url),
                )
                break
            except sqlite3.DatabaseError as e:
                print(f"Exception: {e}. Retrying query...")
                logging.error(
                    "An exception has occurred trying to write on the db: %s. Retrying query...",
                    e,
                )
        logging.info("db entry for url %s updated", url)
    return True


# this one is slower
def check_archive_status_new(db: database.Database, time: datetime.datetime) -> bool:
    """The same but using waybackpy."""
    entries = db.q.execute(
        "SELECT DISTINCT imgur_link FROM imgur_link WHERE archived = 0"
    ).fetchall()
    for entry in entries:
        url = entry["imgur_link"]
        print(f"Checking url: {url}")
        logging.info("Checking url: %s", url)
        availability_api = waybackpy.WaybackMachineAvailabilityAPI(url)
        availability_api.newest()
        if availability_api.json is None:
            status = 2
        else:
            status = 1 if availability_api.timestamp() > time else 3
        print(
            f"Status: {'found' if status==1 else 'old' if status==3 else 'not found'}"
        )
        logging.info("Status of url %s: %s", url, status)
        db.q.execute(
            "UPDATE imgur_link SET archived = ? WHERE imgur_link = ?", (status, url)
        )
        logging.info("db entry for url %s updated", url)
    return True


@ratelimit.sleep_and_retry
@ratelimit.limits(calls=1, period=5)
def archive_url(url: str) -> str:
    """Archive an URL, return the timestamp."""
    save_api = waybackpy.WaybackMachineSaveAPI(url)
    save_api.save()
    return save_api.timestamp()


def send_to_archive(db: database.Database) -> None:
    """Given a table of URLs, send them to the archive."""
    entry = db.q.execute(
        "SELECT url FROM urls WHERE checked = 1 and archived = 0 and url LIKE '%/a/%'"
    ).fetchone()
    if not entry:
        entry = db.q.execute(
            "SELECT url FROM urls WHERE checked = 1 and archived = 0"
        ).fetchone()
    if not entry:
        status = db.q.execute("SELECT COUNT(*) 'num' FROM urls WHERE checked = 0")
        return status["num"] > 0
    url = entry["url"]
    timestamp = is_archived(wayback.WaybackClient(), url)
    if not timestamp:
        print(f"Archiving url: {url}")
        logging.info("Archiving url: %s", url)
        timestamp = archive_url(url)
    logging.info("Page archived")
    while True:
        try:
            db.q.execute(
                "UPDATE urls SET archived = 1, archived_time = ? WHERE url = ?",
                (timestamp, url),
            )
            break
        except sqlite3.DatabaseError as e:
            print(f"Exception: {e}. Retrying query...")
            logging.error(
                "An exception has occurred trying to write on the db: %s. Retrying query...",
                e,
            )
    logging.info("db entry for url %s updated", url)
    return True


def main_check() -> None:
    """Check archiving status."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        handlers=[
            TimedRotatingFileHandler(
                filename="logs\\archive_all_check.log",
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

    while True:
        try:
            if check_archive_status(
                db=database.DatabaseWriting("data\\urls.sqlite"),
            ):
                break
        except ConnectionError:
            continue
        except Exception as e:
            print(f"An exception has occurred: {e}")
            logging.error("An exception has occurred: %s", e)
    logging.info("%s%s", "-" * 60, "\n")


def main_archive() -> None:
    """Archive stuff."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        handlers=[
            TimedRotatingFileHandler(
                filename="logs\\archive_all_archive.log",
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

    while True:
        try:
            status = send_to_archive(
                db=database.DatabaseWriting("data\\urls.sqlite"),
            )
            if not status:
                break
        except ConnectionError:
            continue
        except Exception as e:
            print(f"An exception has occurred: {e}")
            logging.error("An exception has occurred: %s", e)
    logging.info("%s%s", "-" * 60, "\n")


if __name__ == "__main__":
    # main_check()
    main_archive()
