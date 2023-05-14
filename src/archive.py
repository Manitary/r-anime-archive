"""Archive/Wayback machine module."""

import os
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
import ratelimit
import wayback
import waybackpy
import database

logger = logging.getLogger(__name__)

IMGUR_TIME = datetime.datetime(year=2023, month=4, day=19)


def is_archived(
    client: wayback.WaybackClient, time: datetime.datetime, url: str
) -> bool:
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


def check_archive_status(db: database.Database, time: datetime.datetime) -> bool:
    """Given a table of URLs, check whether they have been archived any time from the given date."""
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
@ratelimit.limits(calls=1, period=4)
def archive_url(url: str) -> str:
    """Archive an URL"""
    save_api = waybackpy.WaybackMachineSaveAPI(url)
    save_api.save()


def send_to_archive(db: database.Database) -> None:
    """Given a table of URLs, send them to the archive."""
    entries = db.q.execute(
        "SELECT DISTINCT imgur_link FROM imgur_link WHERE archived = 2"
    ).fetchall()
    for entry in entries:
        url = entry["imgur_link"]
        print(f"Archiving url: {url}")
        logging.info("Archiving url: %s", url)
        archive_url(url)
        logging.info("Page archived")
        db.q.execute("UPDATE imgur_link SET archived = 4 WHERE imgur_link = ?", (url,))
        logging.info("db entry for url %s updated", url)
    return True


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
    # while True:
    #     try:
    #         if check_archive_status(
    #             db=database.DatabaseWriting("data\\rewatches.sqlite"),
    #             time=IMGUR_TIME,
    #         ):
    #             break
    #     except ConnectionError:
    #         continue
    #     except Exception as e:
    #         print(f"An exception has occurred: {e}")
    #         logging.error("An exception has occurred: %s", e)
    send_to_archive(database.DatabaseWriting("data\\writing.sqlite"))
    logging.info("%s%s", "-" * 60, "\n")
