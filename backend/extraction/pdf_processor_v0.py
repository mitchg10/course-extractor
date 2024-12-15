from pathlib import Path
import PyPDF2
import pytesseract
import pdf2image
import logging
from typing import Optional, List
import io
import tempfile
from PIL import Image
import re
from ..utils import PDFProcessingError
import json
from datetime import datetime
from typing import Dict


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format with additional metadata."""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }

        # Add error information if present
        if record.exc_info:
            log_data['error'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # Add custom fields if present
        if hasattr(record, 'pdf_metadata'):
            log_data['pdf_metadata'] = record.pdf_metadata

        if hasattr(record, 'performance_metrics'):
            log_data['performance_metrics'] = record.performance_metrics

        return json.dumps(log_data)


class PDFProcessor:
    """Handles PDF file processing and text extraction with multiple fallback methods."""

    def __init__(self, log_level=logging.INFO):
        # self.logger = logging.getLogger(__name__)
        # Initialize logger with custom name
        self.logger = logging.getLogger('pdf_processor')

        # Create console handler with custom formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())

        # Create file handler for persistent logging
        file_handler = logging.FileHandler('pdf_processing.log')
        file_handler.setFormatter(JSONFormatter())

        # Configure logger
        self.logger.setLevel(log_level)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        # Initialize performance metrics
        self.performance_metrics = {'processing_times': {}}

        # Initialize Tesseract OCR
        self._initialize_tesseract()

    def _initialize_tesseract(self):
        """Initialize Tesseract with configurations."""
        try:
            # Configure tesseract parameters for better table recognition
            custom_config = r'--oem 3 --psm 6'
            version = pytesseract.get_tesseract_version()  # Test if tesseract is installed
            self._log_with_context(
                logging.INFO,
                f"Tesseract initialized successfully with version {version}",
                extra_data={'tesseract_config': custom_config}
            )
        except Exception as e:
            self._log_with_context(
                logging.WARNING,
                "Tesseract not properly configured",
                extra_data={'error': str(e)}
            )

    def _log_with_context(self, level: int, message: str, pdf_path: Optional[Path] = None,
                          extra_data: Optional[Dict] = None):
        """Log messages with additional context."""
        extra = {}

        if pdf_path:
            try:
                extra['pdf_metadata'] = {
                    'filename': pdf_path.name,
                    'size': pdf_path.stat().st_size,
                    'last_modified': datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat()
                }
            except Exception as e:
                extra['pdf_metadata'] = {'error': str(e)}

        if extra_data:
            extra.update(extra_data)

        self.logger.log(level, message, extra={'extra': extra})

    def _extract_with_pypdf(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2."""
        start_time = datetime.now()
        try:
            text = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                self._log_with_context(
                    logging.INFO,
                    f"Starting PyPDF2 extraction on {num_pages} pages",
                    pdf_path,
                    {'num_pages': num_pages}
                )

                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text.append(page_text)

                    self._log_with_context(
                        logging.DEBUG,
                        f"Extracted page {i+1}/{num_pages}",
                        pdf_path,
                        {'page_number': i+1, 'characters_extracted': len(page_text)}
                    )

            elapsed_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics['processing_times'][pdf_path.name] = {
                'method': 'pypdf2',
                'duration': elapsed_time,
                'pages_processed': num_pages
            }

            return '\n'.join(text)

        except Exception as e:
            self._log_with_context(
                logging.ERROR,
                "PyPDF2 extraction failed",
                pdf_path,
                {'error': str(e), 'error_type': type(e).__name__}
            )
            return ""

    def _extract_with_ocr(self, pdf_path: Path) -> str:
        """Extract text using OCR when PyPDF2 fails."""
        start_time = datetime.now()
        text = []

        try:
            # Convert PDF to images
            self._log_with_context(
                logging.INFO,
                "Starting PDF to image conversion",
                pdf_path
            )

            images = pdf2image.convert_from_path(pdf_path)

            self._log_with_context(
                logging.INFO,
                f"Successfully converted PDF to {len(images)} images",
                pdf_path,
                {'num_images': len(images)}
            )

            for i, image in enumerate(images, 1):
                page_start_time = datetime.now()

                self._log_with_context(
                    logging.INFO,
                    f"Processing page {i}/{len(images)} with OCR",
                    pdf_path,
                    {'page_number': i}
                )

                # Log image properties before preprocessing
                original_size = image.size
                original_mode = image.mode
                self._log_with_context(
                    logging.DEBUG,
                    "Original image properties",
                    pdf_path,
                    {
                        'page_number': i,
                        'image_properties': {
                            'size': original_size,
                            'mode': original_mode,
                            'format': image.format
                        }
                    }
                )

                # Enhance image for better OCR
                try:
                    image = self._preprocess_image(image)
                    self._log_with_context(
                        logging.DEBUG,
                        "Image preprocessing completed",
                        pdf_path,
                        {
                            'page_number': i,
                            'preprocessing': {
                                'original_size': original_size,
                                'new_size': image.size,
                                'original_mode': original_mode,
                                'new_mode': image.mode
                            }
                        }
                    )
                except Exception as e:
                    self._log_with_context(
                        logging.ERROR,
                        "Image preprocessing failed",
                        pdf_path,
                        {
                            'page_number': i,
                            'error': str(e),
                            'error_type': type(e).__name__
                        }
                    )
                    continue

                # Perform OCR
                try:
                    page_text = pytesseract.image_to_string(
                        image,
                        config='--oem 3 --psm 6'
                    )

                    # Calculate confidence scores if available
                    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                    confidence_scores = [float(conf) for conf in ocr_data['conf'] if conf != '-1']
                    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

                    page_processing_time = (datetime.now() - page_start_time).total_seconds()

                    self._log_with_context(
                        logging.INFO,
                        f"OCR completed for page {i}",
                        pdf_path,
                        {
                            'page_number': i,
                            'ocr_metrics': {
                                'characters_extracted': len(page_text),
                                'average_confidence': avg_confidence,
                                'processing_time': page_processing_time,
                                'words_detected': len(ocr_data['text']),
                                'low_confidence_words': sum(1 for conf in confidence_scores if conf < 50)
                            }
                        }
                    )

                    text.append(page_text)

                except Exception as e:
                    self._log_with_context(
                        logging.ERROR,
                        f"OCR failed for page {i}",
                        pdf_path,
                        {
                            'page_number': i,
                            'error': str(e),
                            'error_type': type(e).__name__
                        }
                    )
                    continue

            # Calculate and log overall OCR performance
            total_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics['processing_times'][pdf_path.name] = {
                'method': 'ocr',
                'duration': total_time,
                'pages_processed': len(images),
                'average_time_per_page': total_time / len(images) if images else 0
            }

            combined_text = '\n'.join(text)

            self._log_with_context(
                logging.INFO,
                "OCR extraction completed",
                pdf_path,
                {
                    'final_metrics': {
                        'total_pages': len(images),
                        'total_characters': len(combined_text),
                        'total_processing_time': total_time,
                        'successfully_processed_pages': len(text)
                    }
                }
            )

            return combined_text

        except Exception as e:
            self._log_with_context(
                logging.ERROR,
                "OCR extraction failed completely",
                pdf_path,
                {
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'processing_time': (datetime.now() - start_time).total_seconds()
                }
            )
            return ""

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        image = image.convert('L')

        # Increase contrast
        enhancer = Image.enhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Increase sharpness
        enhancer = Image.enhance.Sharpness(image)
        image = enhancer.enhance(2.0)

        return image

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return text

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable())

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove empty lines
        text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())

        return text

    def get_performance_metrics(self) -> Dict:
        """Return performance metrics for monitoring."""
        return self.performance_metrics

    def reset_performance_metrics(self):
        """Reset performance metrics."""
        self.performance_metrics = {'processing_times': {}}

    def process(self, pdf_path: Path) -> str:
        """
        Process a PDF file and extract its text content using multiple methods.

        Args:
            pdf_path (Path): Path to the PDF file

        Returns:
            str: Extracted and cleaned text content

        Raises:
            PDFProcessingError: If all extraction methods fail
        """
        self.logger.info(f"Starting PDF processing: {pdf_path}")

        if not pdf_path.exists():
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")

        # Try PyPDF2 first
        text = self._extract_with_pypdf(pdf_path)

        # If PyPDF2 fails or returns empty text, try OCR
        if not text.strip():
            self.logger.info("PyPDF2 extraction failed, attempting OCR")
            text = self._extract_with_ocr(pdf_path)

        # Clean and normalize the text
        text = self._clean_text(text)

        if not text.strip():
            raise PDFProcessingError("Failed to extract text using all available methods")

        self.logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text

    def validate_output(self, text: str) -> bool:
        """
        Validate the extracted text contains expected course information.

        Args:
            text (str): Extracted text to validate

        Returns:
            bool: True if text appears to contain course information
        """
        # Check for common course-related patterns
        patterns = [
            r'\b[A-Z]{2,4}[-\s]?\d{4}\b',  # Course codes (e.g., CS 1101)
            r'\b(Spring|Fall|Summer)\s+\d{4}\b',  # Semesters
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|M|T|W|R|F)\b',  # Days
            r'\b\d{1,2}:\d{2}\s*(?:AM|PM)\b'  # Times
        ]

        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
