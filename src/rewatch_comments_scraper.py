"""Scrape submissions and comments."""

import pathlib
import json
import pickle
from typing import Any
import praw
from praw.models.reddit.submission import Submission
from praw.models.reddit.comment import Comment
from rewatch_database import Database

BASE_PATH = "data\\rewatch_data"
QUERY_PATH = "src\\queries"


class CommentTreeScraper:
    """The scraper."""

    def __init__(self, config_name: str, db: Database = Database()) -> None:
        """Initialise a Reddit instance for the given bot name.

        The configuration must be in a .ini file in the workspace folder."""
        self._db = db
        self._reddit: praw.Reddit = praw.Reddit(config_name)
        self._submission: Submission = None
        self._comments: list[Comment] = None

    def select_submission(self, submission_id: str) -> None:
        """Pick the submission to scrape.

        Automatically calls ``replace_more()`` to remove all ``MoreComments`` objects
        and get a non-lazy ``Submission`` object."""
        self._submission: Submission = self._reddit.submission(submission_id)
        self._submission.comment_sort = "old"
        self._submission.comments.replace_more(limit=None)
        self._comments = self._submission.comments.list()

    @property
    def all_comments(self) -> list[Comment]:
        """Return all comments of the submission."""
        comments = self._submission.comments
        return comments.list()

    @property
    def id(self) -> str:
        """Return the submission id."""
        if self._submission:
            return self._submission.id
        return None

    def extract_comments(self) -> dict[str, dict]:
        """Return all the comment data."""
        return {comment.id: vars(comment) for comment in self.all_comments}

    def extract_submission(self) -> dict:
        """Return all the submission information."""
        return vars(self._submission)

    @staticmethod
    def submission_to_json(submission: Submission) -> dict:
        """Return a selection of submission attributes that are JSON-ifiable."""
        info = {
            "id": submission.id,
            "author": submission.author.name if submission.author else None,
            "title": submission.title,
            "body": submission.selftext,
            "created": submission.created,
            "created_utc": submission.created_utc,
            "edited": submission.edited,
            "num_comments": submission.num_comments,
            "score": submission.score,
            "upvotes": submission.ups,
            "upvote_ratio": submission.upvote_ratio,
            "gilded": submission.gilded,
            "archived": submission.archived,
        }
        return info

    @staticmethod
    def comment_to_json(comment: Comment) -> dict:
        """Return a selection of comment attributes that are JSON-ifiable."""
        info = {
            "id": comment.id,
            "author": comment.author.name if comment.author else None,
            "body": comment.body,
            "created": comment.created,
            "created_utc": comment.created_utc,
            "edited": comment.edited,
            "upvotes": comment.ups,
            "downvotes": comment.downs,
            "depth": comment.depth,
            "gilded": comment.gilded,
            "parent": comment.parent_id,
        }
        return info

    def comments_to_json(self) -> dict:
        """Return a JSON-ified version of all comments."""
        return {
            comment.id: self.comment_to_json(comment) for comment in self.all_comments
        }

    def dump_all(self) -> None:
        """Dump everything from the current submission."""
        comments_json = self.comments_to_json()
        self.dump_pickle()
        self.dump_json(obj=[self.submission_to_json(self._submission), comments_json])
        self.dump_to_db(comments_json)

    def dump_pickle(self, path: str = BASE_PATH) -> None:
        """Pickle all information.

        The file is named after the submission id."""
        file_path: pathlib.PurePath = pathlib.Path(f"{path}\\dump\\{self.id}.pickle")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("wb") as f:
            print(f"Pickling submission {self.id}")
            pickle.dump([self.extract_submission(), self.extract_comments()], f)

    def dump_json(self, obj: Any, path: str = BASE_PATH) -> None:
        """Dump the information in JSON format.

        The file is named after the submission id."""
        file_path: pathlib.PurePath = pathlib.Path(f"{path}\\json\\{self.id}.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf8") as f:
            print(f"Saving submission {self.id}")
            f.write(json.dumps(obj))

    def dump_to_db(self, comments_data: dict) -> None:
        """Save comment tree into db."""
        relations = (
            (
                self.id,
                comment_id,
                comment["parent"][3:] if comment["parent"].startswith("t1_") else None,
            )
            for comment_id, comment in comments_data.items()
        )
        with open(
            f"{QUERY_PATH}\\add_comment_tree_relations.sql", encoding="utf8"
        ) as f:
            try:
                self._db.q.executemany(f.read(), relations)
                self._db.commit()
            except BaseException as e:
                print(f"Exception: {e}")


def scrape_from_db(config: str, db: Database = Database()) -> None:
    """Scrape"""
    scraper = CommentTreeScraper(config)
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
                scraper.dump_all()
            db.commit()
            print("Comment tree processed")
            db.q.execute("UPDATE rewatch SET processed = 1 WHERE id = ?", (rewatch_id,))
            db.commit()
            print("Rewatch marked as processed")
        except BaseException as e:
            print(f"Exception: {e}")
            db.rollback()


if __name__ == "__main__":
    scrape_from_db("CommentTreeScraper")
