"""
Shared logger instance for all Cryptrix modules.
Uses loguru for structured, colorized output.
"""
from loguru import logger
import sys

logger.remove()  # Remove default handler

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
    level="INFO",
    colorize=True,
)

logger.add(
    "logs/cryptrix.log",
    rotation="50 MB",
    retention="14 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
)

__all__ = ["logger"]
