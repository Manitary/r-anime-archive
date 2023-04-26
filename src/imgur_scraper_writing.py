"""Scrape writing archive imgur links."""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from imgur_scraper import ScraperImgur
from database import DatabaseWriting

PATH = "data\\writing_data"
DB_PATH = "data\\writing.sqlite"
LOG_PATH = "logs\\imgur_scraper_writing.log"

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        handlers=[
            TimedRotatingFileHandler(
                filename=LOG_PATH, when="midnight", backupCount=7, encoding="utf8"
            )
        ],
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )
    logging.info("-" * 60)
    scraper = ScraperImgur(path=PATH, db=DatabaseWriting(path=DB_PATH))
    scraper.scrape()
    logging.info("%s%s", "-" * 60, "\n")
