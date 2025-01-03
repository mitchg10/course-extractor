import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from CourseDataMerger import CourseDataMerger
from pdf_to_text_v5 import process_pdf, filter_graduate_courses, find_underenrolled_classes

import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from pyvt import Timetable


def setup_batch_logger(name):
    """Set up logger with file handler for batch processing."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    fh = logging.FileHandler(log_dir / f'{timestamp}_batch_processing.log')
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Also add console handler for immediate feedback
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def process_department_files(data_dir, term="Fall", year="2024"):
    """
    Process all department PDF files in the given directory.

    Args:
        data_dir (str or Path): Directory containing PDF files
        term (str): Academic term (default: "Fall")
        year (str): Academic year (default: "2024")
    """
    logger = setup_batch_logger('batch_processor')
    data_dir = Path(data_dir)

    # Map terms to codes
    term_codes = {
        "spring": "01",
        "summer i": "06",
        "summer ii": "07",
        "fall": "09",
        "winter": "12"
    }

    term_code = term_codes.get(term.lower())
    if not term_code:
        logger.error(f"Invalid term: {term}")
        return

    term_year = f"{year}{term_code}"

    # Initialize empty list for all graduate courses
    all_graduate_courses = []

    # Process each PDF file
    pdf_files = sorted(data_dir.glob("*.pdf"))

    logger.info(f"\nFound {len(pdf_files)} PDF files in {data_dir}")

    for pdf_path in pdf_files:
        # department = pdf_path.name.split()[0]  # Get department code from filename
        # Files are DEPARTMENT.pdf
        department = pdf_path.stem
        logger.info(f"\nProcessing department: {department}")

        try:
            # Extract data from PDF
            course_data = process_pdf(logger, str(pdf_path))

            # Fetch timetable data
            timetable = Timetable()
            timetable_data = timetable.subject_lookup(
                subject_code=department,
                term_year=term_year,
                open_only=False
            )

            # Create merger instance and merge data
            merger = CourseDataMerger()
            merger.load_pdf_data(course_data)
            merger.load_timetable_data(timetable_data)
            merged_courses = merger.merge_course_data()

            # Filter graduate courses
            graduate_courses = filter_graduate_courses(merged_courses)

            # Add department info
            for course in graduate_courses:
                course['department'] = department

            all_graduate_courses.extend(graduate_courses)

            # Log statistics
            stats = merger.get_statistics()
            logger.info(f"Department {department} statistics:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")

        except Exception as e:
            logger.error(f"Error processing {department}: {str(e)}", exc_info=True)

    # Save all graduate courses to CSV
    if all_graduate_courses:
        output_file = data_dir / f"all_graduate_courses_{term.lower()}_{year}.csv"
        df = pd.DataFrame(all_graduate_courses)
        df.to_csv(output_file, index=False)
        logger.info(f"\nSaved combined graduate courses to {output_file}")

        # Find underenrolled courses across all departments
        underenrolled = find_underenrolled_classes(logger, all_graduate_courses)

        if underenrolled:
            under_file = data_dir / f"underenrolled_courses_{term.lower()}_{year}.csv"
            pd.DataFrame(underenrolled).to_csv(under_file, index=False)
            logger.info(f"Saved underenrolled courses to {under_file}")

    logger.info("\nBatch processing complete!")


if __name__ == "__main__":
    data_directory = input("Enter the directory containing PDF files: ")
    term = input("Enter term (default: Fall): ") or "Fall"
    year = input("Enter year (default: 2024): ") or "2024"

    # data_directory could be in double or single quotes
    data_directory = data_directory.strip('\'"')

    process_department_files(data_directory, term, year)
