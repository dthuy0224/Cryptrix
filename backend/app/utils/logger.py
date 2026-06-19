import logging
import sys
from typing import Any

def setup_logger(name: str = "cryptrix") -> logging.Logger:
    """
    Configures a production-grade structured logger for Cryptrix services.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup multiple times
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Structured console formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.propagate = False
    return logger

# Globally accessible logger instance
logger = setup_logger("cryptrix")
