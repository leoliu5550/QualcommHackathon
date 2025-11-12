from dotenv import load_dotenv

from fileorg.app.organizer import FileOrganizer
from fileorg.logger_config import setup_logger

setup_logger(ENV=load_dotenv())


def main():
    fileorg = FileOrganizer(char_limit=100)
    fileorg.start_organize(root_dir="tests/example_data/202510D")


if __name__ == "__main__":
    main()
