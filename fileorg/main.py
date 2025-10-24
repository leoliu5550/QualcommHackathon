from dotenv import load_dotenv
from loguru import logger

from fileorg.logger_config import setup_logger

setup_logger(ENV=load_dotenv())


def main():
    """
    python -m fileorg.main
    """
    logger("hello world")


if __name__ == "__main__":
    main()
