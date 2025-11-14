import os
import sys
import traceback
from pathlib import Path

from appdirs import user_data_dir
from loguru import logger

FILEORG_ENV = "fileorg"


def setup_logger(ENV=None):
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
    if ENV is None:
        ENV = os.getenv("FILEORG_ENV", "production").lower()  # dev / prod
    else:
        ENV = str(ENV).lower() if ENV else "production"
    IS_DEV = ENV == "development"

    # --- 設定 log 目錄 ---
    if IS_DEV:
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
        if IS_DEV
        else "<level>{message}</level>",
        level="DEBUG" if IS_DEV else "INFO",
        colorize=True,
        backtrace=IS_DEV,
        diagnose=IS_DEV,
    )

    # --- 共用的檔案輸出 ---
    logger.add(
        log_dir / "fileorg_{time:YYYYMMDD}.log",
        rotation="1 week",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        level="DEBUG" if IS_DEV else "INFO",
        colorize=False,
        backtrace=IS_DEV,
        diagnose=IS_DEV,
        serialize=not IS_DEV,  # 生產可用 JSON 結構化輸出
    )

    # --- 捕捉全域例外 ---
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        formatted_exception = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"Uncaught exception:\n{formatted_exception}")

    sys.excepthook = handle_exception

    logger.info(f"Logger initialized in {ENV} mode. Logs stored in: {log_dir}")
    return logger
