from typing import List, Dict, Optional
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path


class CourseDataMerger:
    """
    A class to merge course data from PDF extractions with Timetable API data.

    This class handles the merging of course information extracted from PDFs with
    data from the Timetable API, ensuring data consistency and providing validation.
    """

    def __init__(self):
        self.pdf_data: List[Dict] = []
        self.timetable_data = []
        self.merged_data: List[Dict] = []
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Initialize logger for the CourseDataMerger class."""
        logger = logging.getLogger('course_merger')
        logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)

        # Remove existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()

        # Create file handler with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H_%M_%S')
        fh = logging.FileHandler(f'logs/{timestamp}_course_merger.log')
        fh.setLevel(logging.DEBUG)

        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def load_pdf_data(self, pdf_data: List[Dict]) -> None:
        """
        Load data extracted from PDF.

        Args:
            pdf_data: List of dictionaries containing CRN, seats, and capacity information
        """
        # Validate PDF data structure
        validated_data = []
        for course in pdf_data:
            if self._validate_pdf_course(course):
                validated_data.append(course)
            else:
                self.logger.warning(f"Invalid PDF course data: {course}")

        self.pdf_data = validated_data
        self.logger.info(f"Loaded {len(validated_data)} valid courses from PDF data")

    def load_timetable_data(self, timetable_data: List) -> None:
        """
        Load data from Timetable API.

        Args:
            timetable_data: List of Section objects from Timetable API
        """
        self.timetable_data = timetable_data
        self.logger.info(f"Loaded {len(timetable_data)} courses from Timetable")

        # Log course codes for debugging
        course_codes = [section.course_number for section in timetable_data if hasattr(section, 'course_number')]
        self.logger.debug(f"Course codes from timetable: {course_codes}")

    def merge_course_data(self) -> List[Dict]:
        """
        Merge PDF data with Timetable data based on CRN matching.

        Returns:
            List of merged course dictionaries with combined information
        """
        merged_courses = []
        unmatched_crns = []
        pdf_errors = []
        timetable_errors = []

        # Create a lookup dictionary for PDF data
        pdf_lookup = {str(course['crn']): course for course in self.pdf_data}

        for timetable_course in self.timetable_data:
            try:
                course_info = self._extract_timetable_info(timetable_course)
                crn = str(course_info.get('crn'))

                if not crn:
                    timetable_errors.append("Missing CRN in timetable data")
                    continue

                if crn in pdf_lookup:
                    try:
                        pdf_course = pdf_lookup[crn]
                        merged_course = self._create_merged_course(course_info, pdf_course)
                        if merged_course:
                            merged_courses.append(merged_course)
                    except Exception as e:
                        pdf_errors.append(f"Error merging CRN {crn}: {str(e)}")
                else:
                    unmatched_crns.append(crn)

            except Exception as e:
                timetable_errors.append(f"Error processing timetable course: {str(e)}")

        # Log statistics and errors
        self._log_merge_statistics(merged_courses, unmatched_crns, pdf_errors, timetable_errors)

        self.merged_data = merged_courses
        return merged_courses

    def _validate_pdf_course(self, course: Dict) -> bool:
        """Validate PDF course data structure and values."""
        required_fields = ['crn', 'seats', 'capacity']

        # Check required fields exist
        if not all(field in course for field in required_fields):
            return False

        # Validate data types and values
        try:
            crn = str(course['crn'])
            seats = int(course['seats'])
            capacity = int(course['capacity'])

            # Validate CRN format
            if not (crn.isdigit() and len(crn) == 5):
                return False

            # Validate seats and capacity
            if capacity < 0 or seats < 0 or seats > capacity:
                return False

            return True

        except (ValueError, TypeError):
            return False

    def _extract_timetable_info(self, timetable_course) -> Dict:
        """Extract relevant information from a timetable course object."""
        try:
            course_info = timetable_course.get_info()

            # Normalize and validate the data
            if 'crn' in course_info:
                course_info['crn'] = str(course_info['crn'])

            # Convert time formats if needed
            if 'start_time' in course_info:
                course_info['start_time'] = self._normalize_time(course_info['start_time'])
            if 'end_time' in course_info:
                course_info['end_time'] = self._normalize_time(course_info['end_time'])

            return course_info

        except Exception as e:
            self.logger.error(f"Error extracting timetable info: {str(e)}")
            return {}

    def _create_merged_course(self, course_info: Dict, pdf_course: Dict) -> Optional[Dict]:
        """Create a merged course entry from timetable and PDF data."""
        try:
            merged_course = {
                'crn': course_info.get('crn'),
                'code': course_info.get('code'),
                'name': course_info.get('name'),
                'lecture_type': course_info.get('lecture_type'),
                'modality': course_info.get('modality'),
                'credits': course_info.get('credits'),
                'instructor': course_info.get('instructor'),
                'days': course_info.get('days'),
                'start_time': course_info.get('start_time'),
                'end_time': course_info.get('end_time'),
                'location': course_info.get('location'),
                'exam_type': course_info.get('exam_type'),
                'seats': pdf_course.get('seats'),
                'capacity': pdf_course.get('capacity')
            }

            # Validate merged data
            if self._validate_merged_course(merged_course):
                return merged_course
            return None

        except Exception as e:
            self.logger.error(f"Error creating merged course: {str(e)}")
            return None

    def _validate_merged_course(self, course: Dict) -> bool:
        """Validate the merged course data."""
        required_fields = ['crn', 'code', 'seats', 'capacity']
        return all(course.get(field) is not None for field in required_fields)

    def _normalize_time(self, time_str: Optional[str]) -> Optional[str]:
        """Normalize time format."""
        if not time_str:
            return None

        # Add your time normalization logic here if needed
        return time_str

    def _log_merge_statistics(self, merged_courses: List[Dict], unmatched_crns: List[str],
                              pdf_errors: List[str], timetable_errors: List[str]) -> None:
        """Log detailed statistics about the merge operation."""
        stats = {
            'total_pdf_courses': len(self.pdf_data),
            'total_timetable_courses': len(self.timetable_data),
            'successfully_merged': len(merged_courses),
            'unmatched_crns': len(unmatched_crns),
            'pdf_errors': len(pdf_errors),
            'timetable_errors': len(timetable_errors),
            'match_rate': len(merged_courses) / len(self.timetable_data) if self.timetable_data else 0
        }

        self.logger.info("Merge Statistics:")
        for key, value in stats.items():
            self.logger.info(f"{key}: {value}")

        if unmatched_crns:
            self.logger.warning(f"Unmatched CRNs: {unmatched_crns}")
        if pdf_errors:
            self.logger.error(f"PDF processing errors: {pdf_errors}")
        if timetable_errors:
            self.logger.error(f"Timetable processing errors: {timetable_errors}")

    def save_to_csv(self, output_path: str) -> None:
        """
        Save merged data to CSV file.

        Args:
            output_path: Path to save the CSV file
        """
        if not self.merged_data:
            self.logger.warning("No merged data available to save")
            return

        try:
            # Create directory if it doesn't exist
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to CSV
            df = pd.DataFrame(self.merged_data)
            df.to_csv(output_path, index=False)
            self.logger.info(f"Successfully saved merged data to {output_path}")

            # Log some basic statistics about the saved data
            self.logger.info(f"Saved {len(df)} rows with {len(df.columns)} columns")

        except Exception as e:
            self.logger.error(f"Error saving to CSV: {str(e)}")
            raise

    def get_statistics(self) -> Dict:
        """
        Get statistics about the merged data.

        Returns:
            Dictionary containing various statistics about the data
        """
        stats = {
            'total_pdf_courses': len(self.pdf_data),
            'total_timetable_courses': len(self.timetable_data),
            'total_merged_courses': len(self.merged_data),
            'match_rate': len(self.merged_data) / len(self.timetable_data) if self.timetable_data else 0,
            'timestamp': datetime.now().isoformat()
        }

        # Add some additional analytics if merged data exists
        if self.merged_data:
            df = pd.DataFrame(self.merged_data)
            stats.update({
                'unique_courses': len(df['code'].unique()) if 'code' in df else 0,
                'avg_capacity': df['capacity'].mean() if 'capacity' in df else 0,
                'avg_seats_taken': df['seats'].mean() if 'seats' in df else 0,
            })

        return stats
