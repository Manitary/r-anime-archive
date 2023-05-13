"""Finding and saving imgur links."""

from imgur_parser import ImgurParser
from database import DatabaseDiscussion

PATH = "data\\discussion_data\\json"
IMGUR_QUERY = "src\\queries\\add_imgur_links.sql"

if __name__ == "__main__":
    imgur = ImgurParser(path=PATH, db=DatabaseDiscussion("data\\discussion.sqlite"))
    imgur.process(query_path=IMGUR_QUERY)
