"""
Centralised logging setup.
All modules import `logger` from here so the format is consistent.
"""
import logging
import sys
from datetime import datetime, timezone

from .config import settings


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def setup_logging() -> logging.Logger:
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_build_formatter())
        root.addHandler(handler)

    return logging.getLogger("text_corrector")


logger = setup_logging()
