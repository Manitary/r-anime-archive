"""Scrape submissions and comments."""

from rewatch_database import Database
from scraper_comment_tree import CommentTreeScraper

BASE_PATH = "data\\rewatch_data"
DB_PATH = "data\\rewatches.sqlite"


def scrape_from_db(config_name: str, db: Database) -> None:
    """Scrape"""
    scraper = CommentTreeScraper(config_name=config_name, db=db)
    while True:
        rewatch = db.q.execute(
            "SELECT id FROM rewatch WHERE processed = 0 LIMIT 1"
        ).fetchone()
        if not rewatch:
            print("done")
            break
        rewatch_id = rewatch["id"]
        print(f"Processing rewatch #{rewatch_id}")
        episodes = db.q.execute(
            "SELECT post_id, title FROM episode WHERE id = ?", (rewatch_id,)
        ).fetchall()
        print(f"{len(episodes)} posts found")
        try:
            for episode in episodes:
                print(f"Processing post {episode['title']}")
                scraper.select_submission(episode["post_id"])
                scraper.dump_all(path=BASE_PATH)
            db.commit()
            print("Comment tree processed")
            db.q.execute("UPDATE rewatch SET processed = 1 WHERE id = ?", (rewatch_id,))
            db.commit()
            print("Rewatch marked as processed")
        except BaseException as e:
            print(f"Exception: {e}")
            db.rollback()


if __name__ == "__main__":
    scrape_from_db(config_name="CommentTreeScraper", db=Database(path=DB_PATH))
