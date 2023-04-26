"""Scrape contents of imgur links."""

import configparser
import re
import json
import pathlib
import shutil
import logging
from typing import Iterator
import requests
import ratelimit
from database import Database

logger = logging.getLogger(__name__)

IMAGE_API = "https://api.imgur.com/3/image/"
ALBUM_API = "https://api.imgur.com/3/album/"
IMAGE_ID = re.compile(r"(?:https:\/\/|http:\/\/|i\.)imgur.com\/(\w+)(?:\.\w+)?")
ALBUM_ID = re.compile(r"(?:https:\/\/|http:\/\/|i\.)imgur.com\/a\/(\w+)")
STACK_ID = re.compile(r"i\.stack\.imgur\.com\/(\w+(?:\.\w+)?)")
FILE_TYPE = re.compile(r"\w+\/(\w+)")

DEFAULT_TIMEOUT = 60
CALLS = 12500
PERIOD = 86400


@ratelimit.sleep_and_retry
@ratelimit.limits(calls=CALLS, period=PERIOD)
def check_limit() -> None:
    """Empty function to check for rate limits."""


class ScraperImgur:
    """The scraper."""

    def __init__(self, path: str, db: Database) -> None:
        config = configparser.ConfigParser()
        config.read("config.ini")
        self._client_id = config["imgur"]["client_id"]
        self._path = path
        self._db = db

    def get_links(self) -> Iterator[str]:
        """Get the list of links from the database."""
        entries = self._db.q.execute(
            "SELECT DISTINCT imgur_link FROM imgur_link WHERE processed = 0"
        ).fetchall()
        for entry in entries:
            link = entry["imgur_link"]
            print(f"New link found: {link}")
            yield link

    def scrape(self) -> None:
        """Scrape the links."""
        for link in self.get_links():
            self._db.begin()
            try:
                self.download_link(link)
                self._db.q.execute(
                    "UPDATE imgur_link SET processed = 1 WHERE imgur_link = ?", (link,)
                )
                self._db.commit()
            except Exception as e:
                print(f"An exception has occurred: {e}")
                logger.error(
                    "An exception has occurred when processing %s: %s", link, e
                )
                self._db.rollback()

    def download_link(self, url: str) -> None:
        """Download the given imgur link.

        Distinguish behaviour between image link and album link,
        as well as 'deprecated' link types (e.g. i.stacks.imgur.com)."""
        # Edge cases links
        if file_name := STACK_ID.match(url):
            self.download_special(url, file_name.group(0))
            return
        # Album link
        if album_id := ALBUM_ID.search(url):
            self.download_album(album_id.group(1))
            return
        # Image link
        if image_id := IMAGE_ID.search(url):
            image_data = self.download_image_data(image_id.group(1))
            self.download_image(image_data)
            return

    def download_image_data(self, image_id: str) -> dict:
        """Download image data from imgur given its id."""
        check_limit()
        r = requests.get(
            f"{IMAGE_API}{image_id}",
            headers={"Authorization": f"Client-ID {self._client_id}"},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            print("Error code: ", r.status_code)
            logger.error(
                "The image with id %s returned error code %s",
                image_id,
                r.status_code,
            )
            raise ValueError(f"Image {image_id} returned error code {r.status_code}")

        return r.json()["data"]

    @ratelimit.sleep_and_retry
    @ratelimit.limits(calls=1, period=2)
    def download_image(self, image_data: dict) -> None:
        """Download an image and its data from imgur."""
        image_url = image_data["link"]
        image_id = image_data["id"]
        file_type = FILE_TYPE.search(image_data["type"]).group(1)
        data_path = pathlib.Path(f"{self._path}\\image_data\\{image_id}.json")
        file_path = pathlib.Path(f"{self._path}\\images\\{image_id}.{file_type}")
        data_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url=image_url, timeout=DEFAULT_TIMEOUT, stream=True)
        if r.status_code != 200:
            print("Error code: ", r.status_code)
            logger.error(
                "The image at url %s returned error code %s", image_url, r.status_code
            )
            raise ValueError(f"The url {image_url} returned error code {r.status_code}")

        with file_path.open("wb") as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        with data_path.open("w", encoding="utf8") as f:
            f.write(json.dumps(image_data))
        print(f"Image at {image_url} downloaded to {file_path}.")

    def download_album(self, album_id: str) -> dict:
        """Download album data from imgur given its id."""
        check_limit()
        r = requests.get(
            f"{ALBUM_API}{album_id}",
            headers={"Authorization": f"Client-ID {self._client_id}"},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            print("Error code: ", r.status_code)
            logger.error(
                "The album with id %s returned error code %s",
                album_id,
                r.status_code,
            )
            raise ValueError(f"Album {album_id} returned error code {r.status_code}")

        album_data = r.json()["data"]
        print(f"Processing album {album_id}")
        for image in album_data["images"]:
            self.download_image(image)
        # Keep only image IDs, as their other data is stored separately.
        album_data["images"] = [image["id"] for image in album_data["images"]]
        data_path = pathlib.Path(f"{self._path}\\album_data\\{album_id}.json")
        data_path.parent.mkdir(parents=True, exist_ok=True)
        with data_path.open("w", encoding="utf8") as f:
            f.write(json.dumps(album_data))
        print(f"Album complete, data downloaded to {data_path}.")

    def download_special(self, image_url: str, file_name: str) -> None:
        """Special downloads that do not follow usual rules."""
        file_path = pathlib.Path(f"{self._path}\\special\\{file_name}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        check_limit()
        r = requests.get(
            url=f"http://{image_url}", timeout=DEFAULT_TIMEOUT, stream=True
        )
        if r.status_code != 200:
            print("Error code: ", r.status_code)
            logger.error(
                "The image at url %s returned error code %s", image_url, r.status_code
            )
            raise ValueError(f"The url {image_url} returned error code {r.status_code}")

        with file_path.open("wb") as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        print(f"Image at {image_url} downloaded to {file_path}.")
