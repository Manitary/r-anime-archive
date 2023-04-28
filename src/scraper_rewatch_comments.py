"""Scrape submissions and comments."""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from database import DatabaseRewatch
from scraper_comment_tree import CommentTreeScraper

BASE_PATH = "data\\rewatch_data"
DB_PATH = "data\\rewatches.sqlite"


def scrape_from_db(config_name: str, db: DatabaseRewatch) -> None:
    """Scrape"""
    scraper = CommentTreeScraper(config_name=config_name, db=db)
    rewatches = db.q.execute("SELECT id FROM rewatch WHERE processed = 0").fetchall()
    if not rewatches:
        print("done")
        return
    logging.info("%s rewatches to process found", len(rewatches))
    for rewatch in rewatches:
        rewatch_id = rewatch["id"]
        print(f"Processing rewatch #{rewatch_id}")
        episodes = db.q.execute(
            "SELECT post_id, title FROM episode WHERE id = ?", (rewatch_id,)
        ).fetchall()
        print(f"{len(episodes)} posts found")
        logging.info(
            "Processing rewatch #%s, %s posts found", rewatch_id, len(episodes)
        )
        db.begin()
        try:
            for episode in episodes:
                print(f"Processing post {episode['title']}")
                scraper.select_submission(episode["post_id"])
                scraper.dump_all(path=BASE_PATH)
                logging.info(
                    "Comment tree for rewatch #%s - submission %s (%s) processed",
                    rewatch_id,
                    episode["post_id"],
                    episode["title"],
                )
            print("Comment tree processed")
            logging.info("Comment trees for rewatch #%s processed", rewatch_id)
            db.q.execute("UPDATE rewatch SET processed = 1 WHERE id = ?", (rewatch_id,))
            db.commit()
            print("Rewatch marked as processed")
            logging.info("Rewatch #%s marked as processed", rewatch_id)
        except Exception as e:
            print(f"Exception: {e}")
            logging.error(
                "An exception has occurred while processing rewatch #%s: %s",
                rewatch_id,
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
    scrape_from_db(config_name="CommentTreeScraper", db=DatabaseRewatch(path=DB_PATH))
    logging.info("-" * 60)
