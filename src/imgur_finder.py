"""Find, download, and map all imgur links in the given path."""

import pathlib
import glob
import re

IMGUR = re.compile(r"\[([^\[\]]*)\]\(([^\(]*imgur\.com[^\)]*)\)")


class Imgur:
    """The imgur links extractor."""

    def __init__(self, path: str) -> None:
        """Initialise the imgur finder at the given path."""
        self._path = path
        self._file_path: pathlib.PurePath = pathlib.Path(f"{path}\\imgur_links.txt")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def trim_file_path(self, file_path: str) -> str:
        """Remove the local folder structure, as well as the txt extension."""
        return file_path[len(self._path) : -4]

    def generate_links(self, recursive: bool = True) -> None:
        """Create a file with the links."""
        files = glob.iglob(f"{self._path}**.txt", recursive=recursive)
        with self._file_path.open("w", encoding="utf8") as g:
            for file_name in files:
                print(f"Checking: {file_name}")
                links = self.get_links_from_file(file_name)
                if links:
                    g.write(
                        f"{self.trim_file_path(file_name)}\n{self.format_list(links)}\n\n"
                    )

    @staticmethod
    def format_list(entries: tuple) -> str:
        """String format to display the list of links."""
        return "\n".join(f"{link} - {text}" for text, link in entries)

    @staticmethod
    def get_links_from_file(file_name: str) -> list[str]:
        """Return the list of imgur links in the given file."""
        with open(file_name, encoding="utf8") as f:
            contents = f.read()
        return IMGUR.findall(contents)


if __name__ == "__main__":
    imgur = Imgur("data\\wiki\\anime\\")
    imgur.generate_links()
