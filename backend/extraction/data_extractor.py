# Updated data_extractor.py to align with pdf_to_text_v4.py logic

from typing import Dict, List
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
from pyvt import Timetable  # Importing pyvt library for timetable integration

class DataExtractor:
    """
    Processes extracted course data, validating and merging as needed.
    Includes dynamic fetching of timetable data using pyvt.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path("data/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_courses(self, course_data: List[Dict]) -> List[Dict]:
        """
        Validate and process course data extracted from PDF.

        Args:
            course_data (List[Dict]): List of course dictionaries from PDFProcessor.

        Returns:
            List[Dict]: Processed and validated course information.
        """
        if not course_data:
            self.logger.warning("No course data provided for extraction.")
            return []

        validated_courses = []
        for course in course_data:
            if self._validate_course(course):
                validated_courses.append(course)
            else:
                self.logger.debug(f"Invalid course data skipped: {course}")

        self._save_to_csv(validated_courses)
        return validated_courses

    def _validate_course(self, course: Dict) -> bool:
        """
        Validate individual course data based on required fields.

        Args:
            course (Dict): Extracted course data.

        Returns:
            bool: True if valid, False otherwise.
        """
        required_fields = ["CRN", "Seats", "Capacity"]
        return all(field in course and isinstance(course[field], (int, str)) for field in required_fields)

    def _save_to_csv(self, course_data: List[Dict]):
        """
        Save validated course data to a timestamped CSV file.

        Args:
            course_data (List[Dict]): List of validated course dictionaries.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"processed_courses_{timestamp}.csv"

        try:
            df = pd.DataFrame(course_data)
            df.to_csv(output_file, index=False)
            self.logger.info(f"Saved processed data to {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save course data to CSV: {str(e)}")

    def fetch_timetable_data(self, subject_code: str, term_year: str) -> List[Dict]:
        """
        Fetch timetable data dynamically using pyvt.

        Args:
            subject_code (str): The subject code to query (e.g., "CS").
            term_year (str): The term and year (e.g., "202409").

        Returns:
            List[Dict]: Retrieved timetable data.
        """
        self.logger.info(f"Fetching timetable data for subject: {subject_code}, term: {term_year}")
        timetable = Timetable()
        sections = timetable.subject_lookup(subject_code=subject_code, term_year=term_year, open_only=False)
        return [section.get_info() for section in sections]

    def merge_with_timetable(self, pdf_courses: List[Dict], subject_code: str, term_year: str) -> List[Dict]:
        """
        Merge PDF-extracted courses with timetable data based on CRN.

        Args:
            pdf_courses (List[Dict]): Courses extracted from PDFs.
            subject_code (str): The subject code for timetable query.
            term_year (str): The term and year for timetable query.

        Returns:
            List[Dict]: Merged course data.
        """
        timetable_courses = self.fetch_timetable_data(subject_code, term_year)
        merged_courses = []
        timetable_lookup = {str(course['CRN']): course for course in timetable_courses}

        for pdf_course in pdf_courses:
            crn = str(pdf_course.get("CRN"))
            timetable_course = timetable_lookup.get(crn)

            if timetable_course:
                merged_course = {**timetable_course, **pdf_course}
                merged_courses.append(merged_course)
            else:
                self.logger.warning(f"Unmatched course for CRN: {crn}")

        self.logger.info(f"Successfully merged {len(merged_courses)} courses.")
        return merged_courses

    def get_processed_files(self) -> List[Path]:
        """
        List all processed course data files.

        Returns:
            List[Path]: List of file paths to processed CSVs.
        """
        return sorted(self.output_dir.glob("processed_courses_*.csv"))
