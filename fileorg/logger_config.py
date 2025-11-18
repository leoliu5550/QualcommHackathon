import os
import sys
import traceback
from pathlib import Path

from appdirs import user_data_dir
from loguru import logger

FILEORG_ENV = "fileorg"


def setup_logger():
    """Initializes the Loguru logger with specific settings for development and production.

    The logging setup includes:
    1. Determining the execution environment (development or production).
    2. Setting up the log file directory.
    3. Configuring console output (only for development mode).
    4. Configuring file output (with rotation, retention, and compression).
    5. Overriding the default exception hook to capture uncaught exceptions.

    Args:
        ENV: Optional environment override. If None, reads from FILEORG_ENV env var.

    Returns:
        The configured loguru.logger instance.
    """
    # ENV is typically a boolean from load_dotenv(), but we always read from env var
    # regardless of whether .env was successfully loaded
    env_value = os.getenv("FILEORG_ENV", "production").lower()  # dev / prod
    is_dev = env_value == "development"

    # --- 設定 log 目錄 ---
    if env_value != "production":
        log_dir = Path("logs")
    else:
        log_dir = Path(user_data_dir(FILEORG_ENV)) / "logs"
        # if is production then log would be at ~/Library/Application\ Support/fileorg/logs

    log_dir.mkdir(parents=True, exist_ok=True)

    # --- 移除預設 handler ---
    logger.remove()

    # --- Console 輸出（所有模式） ---
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
        if is_dev
        else "<level>{message}</level>",
        level="DEBUG" if is_dev else "ERROR",
        colorize=True,
        backtrace=is_dev,
        diagnose=is_dev,
    )

    # --- 共用的檔案輸出 ---
    logger.add(
        log_dir / "fileorg_{time:YYYYMMDD}.log",
        rotation="1 week",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        level="DEBUG" if is_dev else "INFO",
        colorize=False,
        backtrace=is_dev,
        diagnose=is_dev,
        serialize=not is_dev,  # 生產可用 JSON 結構化輸出
    )

    # --- 捕捉全域例外 ---
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        formatted_exception = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"Uncaught exception:\n{formatted_exception}")

    sys.excepthook = handle_exception

    logger.info(f"Logger initialized in {env_value} mode. Logs stored in: {log_dir}")
    return logger
