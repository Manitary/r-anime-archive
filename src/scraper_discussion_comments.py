"""Scrape submissions and comments."""

import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from database import DatabaseDiscussion
from scraper_comment_tree import CommentTreeScraper

BASE_PATH = "data\\discussion_data"
DB_PATH = "data\\discussion.sqlite"


def scrape_from_db(config_name: str, db: DatabaseDiscussion) -> None:
    """Scrape"""
    scraper = CommentTreeScraper(config_name=config_name, db=db)
    discussions = db.q.execute(
        "SELECT id FROM discussion WHERE processed = 0"
    ).fetchall()
    if not discussions:
        print("done")
        return
    logging.info("%s discussions to process found", len(discussions))
    for series in discussions:
        series_id = series["id"]
        print(f"Processing series #{series_id}")
        episodes = db.q.execute(
            "SELECT post_id, title FROM episode WHERE id = ?", (series_id,)
        ).fetchall()
        print(f"{len(episodes)} posts found")
        logging.info("Processing series #%s, %s posts found", series_id, len(episodes))
        db.begin()
        try:
            for episode in episodes:
                print(f"Processing post {episode['title']}")
                scraper.select_submission(episode["post_id"])
                scraper.dump_all(path=BASE_PATH)
                logging.info(
                    "Comment tree for series #%s - submission %s (%s) processed",
                    series_id,
                    episode["post_id"],
                    episode["title"],
                )
            print("Comment tree processed")
            logging.info("Comment trees for series #%s processed", series_id)
            db.q.execute(
                "UPDATE discussion SET processed = 1 WHERE id = ?", (series_id,)
            )
            db.commit()
            print("Series marked as processed")
            logging.info("Series #%s marked as processed", series_id)
        except Exception as e:
            print(f"Exception: {e}")
            logging.error(
                "An exception has occurred while processing series #%s: %s",
                series_id,
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
        level=logging.INFO,
    )
    sys.setrecursionlimit(3000)
    scrape_from_db(
        config_name="CommentTreeScraper", db=DatabaseDiscussion(path=DB_PATH)
    )
    logging.info("-" * 60)
