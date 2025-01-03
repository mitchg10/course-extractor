#!/usr/bin/env python3
import os
import uuid
from pathlib import Path
import shutil
import argparse
from app.core.pdf_processor import PdfProcessor
from app.utils.logger import setup_logger


def test_processor(pdf_path: str, subject_code: str, term_year: str):
    """
    Test the PDF processor with a single file
    """
    # Setup logger
    logger = setup_logger("test_processor")
    logger.info(f"Testing processor with file: {pdf_path}")

    # Create a temporary directory for processing
    task_id = str(uuid.uuid4())
    temp_dir = Path("uploads") / task_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Copy file to temporary directory
        pdf_name = Path(pdf_path).name
        temp_file_path = temp_dir / pdf_name
        shutil.copy2(pdf_path, temp_file_path)

        # Prepare metadata like in the /process endpoint
        file_metadata = [{
            'file_path': str(temp_file_path),
            'subject_code': subject_code,
            'term_year': term_year
        }]

        # Create mock processing_tasks dict
        processing_tasks = {}

        # Initialize processor
        processor = PdfProcessor()

        # Process the file
        logger.info("Starting processing...")
        processor.process_pdf_files(task_id, file_metadata, processing_tasks)

        # Check results
        if task_id in processing_tasks:
            status = processing_tasks[task_id]
            logger.info(f"Processing completed with status: {status['status']}")
            if status.get('error'):
                logger.error(f"Processing error: {status['error']}")
            if status.get('result'):
                logger.info(f"Processing results: {status['result']}")
        else:
            logger.error("No processing status found")

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='Test PDF Processor')
    # parser.add_argument('pdf_path', help='Path to the PDF file to process')
    # parser.add_argument('subject_code', help='Subject code (e.g., CS, ECE)')
    # parser.add_argument('term_year', help='Term year (e.g., 202501 for Spring 2025)')

    # args = parser.parse_args()

    pdf_path = "/Users/mitchellgerhardt/Library/CloudStorage/OneDrive-VirginiaTech/2. Research/GPS/Spring 2025 Data/AOE.pdf"
    subject_code = "AOE"
    term_year = "202501"

    test_processor(pdf_path, subject_code, term_year)
