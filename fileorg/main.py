from dotenv import load_dotenv
from loguru import logger

# from fileorg.app.orchestrator import Orchestrator
from fileorg.app.organizer import FileOrganizer
from fileorg.cli.argument_parser import build_parser
from fileorg.logger_config import setup_logger

setup_logger(ENV=load_dotenv())


def main():
    parser = build_parser()
    args = parser.parse_args()
    logger.debug(f"args id {args}")
    fileorg = FileOrganizer(args=args)
    fileorg.run()


if __name__ == "__main__":
    main()
