"""
Course Data Extractor Backend
----------------------------
A FastAPI-based backend service for extracting course data from PDF timetables.
"""

import logging
from pathlib import Path

__version__ = '0.1.0'
__author__ = 'Mitch Gerhardt - mitchg@vt.edu'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create necessary directories
BACKEND_DIR = Path(__file__).parent
DATA_DIR = BACKEND_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / 'individual').mkdir(exist_ok=True)
(DATA_DIR / 'combined').mkdir(exist_ok=True)