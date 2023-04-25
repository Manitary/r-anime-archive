"""Scrape submissions and comments."""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from database import DatabaseWriting
from scraper_comment_tree import CommentTreeScraper

BASE_PATH = "data\\writing_data"
DB_PATH = "data\\writing.sqlite"


def scrape_from_db(config_name: str, db: DatabaseWriting) -> None:
    """Scrape."""
    scraper = CommentTreeScraper(config_name=config_name, db=db)
    writings = db.q.execute(
        "SELECT id, post_id FROM writing WHERE processed = 0"
    ).fetchall()
    if not writings:
        print("done")
        return
    logging.info("%s writing posts to process found", len(writings))
    for writing in writings:
        writing_id = writing["id"]
        post_id = writing["post_id"]
        print(f"Processing writing post #{writing_id} ({post_id})")
        db.begin()
        try:
            scraper.select_submission(post_id)
            scraper.dump_all(path=BASE_PATH)
            logging.info(
                "Comment tree for writing post #%s (%s) processed", writing_id, post_id
            )
            print("Comment tree processed")
            db.q.execute("UPDATE writing SET processed = 1 WHERE id = ?", (writing_id,))
            db.commit()
            print("Post marked as processed")
            logging.info("Writing post #%s marked as processed", writing_id)
        except Exception as e:
            print(f"Exception: {e}")
            logging.error(
                "An exception has occurred while processing writing post #%s: %s",
                writing_id,
                e,
            )
            db.rollback()
    return


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
    scrape_from_db(config_name="CommentTreeScraper", db=DatabaseWriting(path=DB_PATH))
    logging.info("-" * 60)
