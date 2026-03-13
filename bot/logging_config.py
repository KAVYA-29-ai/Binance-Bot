"""
bot/logging_config.py
=====================
Centralised logging setup for the trading bot.

Two handlers are configured:
  - FileHandler  : writes DEBUG+ records to  logs/trading_bot_YYYYMMDD.log
  - StreamHandler: writes INFO+  records to  the terminal

Usage:
    from bot.logging_config import setup_logger
    logger = setup_logger()
    logger.info("Bot started")
"""

import logging
import os
from datetime import datetime


def setup_logger(
    name: str = "trading_bot",
    log_dir: str = "logs",
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
) -> logging.Logger:
    """
    Build and return a configured Logger.

    Args:
        name         : Logger / log-file name prefix.
        log_dir      : Folder where .log files are stored (created if absent).
        file_level   : Minimum level written to the log file.
        console_level: Minimum level printed to the terminal.

    Returns:
        logging.Logger: Ready-to-use logger instance.
    """
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(
        log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # master level — handlers filter further

    # Prevent duplicate handlers when module is imported multiple times
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── File handler ──────────────────────────────────────────────────────────
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(file_level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # ── Console handler ───────────────────────────────────────────────────────
    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    logger.debug("Logger initialised — file: %s", log_path)
    return logger
