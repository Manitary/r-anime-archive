"""Finding and saving imgur links."""

from imgur_parser import ImgurParser
from database import DatabaseWriting

PATH = "data\\writing_data\\json"
IMGUR_QUERY = "src\\queries\\writing\\add_imgur_links.sql"

if __name__ == "__main__":
    imgur = ImgurParser(path=PATH, db=DatabaseWriting("data\\writing.sqlite"))
    imgur.process(query_path=IMGUR_QUERY)
