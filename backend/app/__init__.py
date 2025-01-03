from .config import Settings
from .utils.logger import setup_logger

__version__ = "0.1.0"

# Initialize settings and logger at package level
settings = Settings()
logger = setup_logger("course_extractor")

# backend/app/api/__init__.py
from .api.models import ProcessingResponse, ProcessingStatus

__all__ = ["ProcessingResponse", "ProcessingStatus"]

# backend/app/core/__init__.py
from .core.pdf_processor import PdfProcessor

__all__ = ["PdfProcessor"]

# backend/app/utils/__init__.py
from .utils.logger import setup_logger

__all__ = ["setup_logger"]