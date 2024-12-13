import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class PDFProcessingError(Exception):
    """Raised when there's an error processing a PDF file."""
    pass

class ValidationError(Exception):
    """Raised when there's a validation error."""
    pass

class DataExtractionError(Exception):
    """Raised when there's an error extracting data."""
    pass

def handle_extraction_error(error: Exception) -> Dict[str, Any]:
    """
    Handle errors during PDF extraction and processing.
    
    Args:
        error (Exception): The caught exception
        
    Returns:
        Dict[str, Any]: Error response details
    """
    logger.error(f"Error occurred: {str(error)}", exc_info=True)
    
    error_response = {
        "status": "error",
        "message": str(error),
        "type": error.__class__.__name__
    }
    
    if isinstance(error, PDFProcessingError):
        error_response["code"] = "PDF_PROCESSING_ERROR"
    elif isinstance(error, ValidationError):
        error_response["code"] = "VALIDATION_ERROR"
    elif isinstance(error, DataExtractionError):
        error_response["code"] = "DATA_EXTRACTION_ERROR"
    else:
        error_response["code"] = "UNKNOWN_ERROR"
    
    return error_response