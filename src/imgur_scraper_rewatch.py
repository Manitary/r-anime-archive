"""Scrape rewatch archive imgur links."""

import os
import itertools
import logging
from logging.handlers import TimedRotatingFileHandler
from imgur_scraper import ScraperImgur
from database import DatabaseRewatch

PATH = "data\\rewatch_data"
DB_PATH = "data\\rewatches.sqlite"
LOG_PATH = "logs\\imgur_scraper_rewatch.log"

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
        level=logging.INFO,
    )
    for i in itertools.count(start=1):
        logging.info("-" * 60)
        logging.info("Connecting with app credentials #%s", i)
        scraper = ScraperImgur(path=PATH, db=DatabaseRewatch(path=DB_PATH), config_id=i)
        scraper.scrape()
        logging.info("%s%s", "-" * 60, "\n")
