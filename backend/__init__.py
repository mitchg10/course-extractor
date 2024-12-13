"""
Course Data Extractor Backend
----------------------------
A FastAPI-based backend service for extracting course data from PDF timetables.

This module initializes the backend environment, setting up:
- Project directory structure
- Logging configuration
- Environment variables
- Version tracking
"""

import logging
import logging.config
import json
from pathlib import Path
import sys
from typing import Dict

__version__ = '0.1.0'
__author__ = 'Mitch Gerhardt - mitchg@vt.edu'

# Define project structure


class ProjectPaths:
    """Container for project-related paths"""

    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.project_root = self.backend_dir.parent

        # Main directories
        self.data_dir = self.project_root / 'data'
        self.logs_dir = self.project_root / 'logs'
        self.config_dir = self.project_root / 'config'

        # Data subdirectories
        self.individual_dir = self.data_dir / 'individual'
        self.combined_dir = self.data_dir / 'combined'

        # Ensure all directories exist
        self._create_directories()

    def _create_directories(self):
        """Create all necessary project directories"""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.individual_dir,
            self.combined_dir,
            self.config_dir
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Initialize project paths
paths = ProjectPaths()


def setup_logging() -> None:
    """Initialize logging configuration"""
    log_config_path = paths.config_dir / 'logging_config.json'

    try:
        if log_config_path.exists():
            # Load custom logging configuration
            with open(log_config_path) as f:
                config = json.load(f)

            # Update log file paths to use project structure
            for handler in config.get('handlers', {}).values():
                if 'filename' in handler:
                    handler['filename'] = str(paths.logs_dir / handler['filename'])

            logging.config.dictConfig(config)
        else:
            # Fallback logging configuration
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(paths.logs_dir / 'app.log'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
    except Exception as e:
        # Emergency logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logging.error(f"Failed to configure logging: {str(e)}")


def get_project_info() -> Dict[str, str]:
    """Return basic project information"""
    return {
        'version': __version__,
        'author': __author__,
        'backend_dir': str(paths.backend_dir),
        'data_dir': str(paths.data_dir),
        'logs_dir': str(paths.logs_dir)
    }


# Initialize logging
setup_logging()

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info(f"Initializing Course Data Extractor Backend v{__version__}")

# Log project setup information
logger.info("Project directories initialized", extra={'paths': get_project_info()})

# Make paths available to other modules
__all__ = ['paths', 'get_project_info', '__version__', '__author__']
