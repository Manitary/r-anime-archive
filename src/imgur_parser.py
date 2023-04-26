"""Finding and saving imgur links."""

import json
import re
import glob
import pathlib
import itertools
from database import Database

IMGUR = re.compile(
    r"((?:https:\/\/|http:\/\/|i\.|i\.stack\.)imgur.com\/(?:a\/)?\w+(?:\.\w+)?)"
)


class ImgurParser:
    """Imgur links parsing and storing into db."""

    def __init__(self, path: str, db: Database) -> None:
        self._db = db
        self._path = path

    def process(self, query_path: str) -> None:
        """Process the files in _path"""
        with open(query_path, encoding="utf8") as f:
            query = f.read()
        for n, file_path in enumerate(glob.iglob(f"{self._path}\\*"), 1):
            print(f"Processing #{n}: {post_id(file_path)}")
            data = parse_file(file_path)
            self._db.q.executemany(
                query,
                data,
            )
        print("done")


def post_id(path: str) -> str:
    """Get the submission id from file name."""
    return pathlib.Path(path).stem


def parse_file(path: str) -> itertools.chain:
    """Do the thing."""
    post, comments = parse_json(path)
    data = itertools.chain(
        process_comment(post),
        *(
            stuff
            for comment in comments.values()
            if (stuff := process_comment(comment))
        ),
    )
    return data


def process_comment(comment: dict) -> tuple[str, int, str]:
    """Process a comment and return the corresponding data to insert into the db."""
    links = find_imgur_links(comment["body"])
    is_submission = 0 if "depth" in comment else 1
    return ((comment["id"], is_submission, link) for link in links)


def parse_json(file_path: str) -> None:
    """parse json file."""
    with open(file_path, encoding="utf8") as f:
        post, comments = json.load(f)
    return post, comments


def find_imgur_links(text: str) -> None:
    """Return the unique imgur links contained in a comment."""
    return set(IMGUR.findall(text))
