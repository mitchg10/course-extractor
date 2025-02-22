# backend/app/utils/logger.py
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
import sys
from ..config import Settings

settings = Settings()

def setup_logger(name: str, log_dir: str = "backend") -> logging.Logger:
    """
    Set up logger with both file and console handlers
    """
    # Create logs directory if it doesn't exist
    if log_dir == "frontend":
        log_dir = settings.LOGS_DIR / "frontend"
    else:
        log_dir = settings.LOGS_DIR / "backend"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = RotatingFileHandler(
        log_dir / f"{name}.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger