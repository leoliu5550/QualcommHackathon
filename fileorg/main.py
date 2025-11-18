from dotenv import load_dotenv
from loguru import logger

from fileorg.app.file_coordinator import FileCoordinator
from fileorg.cli.adapters.progress_display import ProgressDisplay
from fileorg.cli.argument_parser import build_parser, parse_args_to_dataclass
from fileorg.logger_config import setup_logger

load_dotenv()
setup_logger()


def main():
    parser = build_parser()
    args = parser.parse_args()
    args_dataclass = parse_args_to_dataclass(args=args)
    logger.debug(f"args_dataclass {args_dataclass}")
    progress = ProgressDisplay()
    fileorg = FileCoordinator(args=args_dataclass, progress=progress)
    logger.debug(f"args id {args}")
    fileorg.run()


if __name__ == "__main__":
    main()
