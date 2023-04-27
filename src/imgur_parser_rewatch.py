"""Finding and saving imgur links."""

from imgur_parser import ImgurParser
from database import DatabaseRewatch

PATH = "data\\rewatch_data\\json"
IMGUR_QUERY = "src\\queries\\add_imgur_links.sql"

if __name__ == "__main__":
    imgur = ImgurParser(path=PATH, db=DatabaseRewatch("data\\rewatches.sqlite"))
    imgur.process(query_path=IMGUR_QUERY)
