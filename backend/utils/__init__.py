"""
Utility functions and error handling for the Course Extractor.
"""

from .error_handler import (
    handle_extraction_error,
    PDFProcessingError,
    ValidationError,
    DataExtractionError
)

__all__ = [
    'handle_extraction_error',
    'PDFProcessingError',
    'ValidationError',
    'DataExtractionError'
]
