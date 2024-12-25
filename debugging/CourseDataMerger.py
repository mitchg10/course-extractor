import pandas as pd
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CourseDataMerger:
    def __init__(self):
        self.pdf_data = []
        self.timetable_data = []
        self.merged_data = []

    def load_pdf_data(self, pdf_data: List[Dict]):
        """
        Load data extracted from PDF
        Args:
            pdf_data: List of dictionaries containing CRN, seats, and capacity
        """
        self.pdf_data = pdf_data
        logger.info(f"Loaded {len(pdf_data)} courses from PDF data")

    def load_timetable_data(self, timetable_data: List):
        """
        Load data from Timetable API
        Args:
            timetable_data: List of Section objects from Timetable
        """
        self.timetable_data = timetable_data
        logger.info(f"Loaded {len(timetable_data)} courses from Timetable")

    def merge_course_data(self) -> List[Dict]:
        """
        Merge PDF data with Timetable data based on CRN matching
        Returns:
            List of merged course dictionaries with combined information
        """
        merged_courses = []
        unmatched_crns = []

        # Create a lookup dictionary for PDF data
        pdf_lookup = {str(course['crn']): course for course in self.pdf_data}

        for timetable_course in self.timetable_data:
            course_info = timetable_course.get_info()
            crn = str(course_info.get('crn'))

            if crn in pdf_lookup:
                # Found a match - combine the data
                pdf_course = pdf_lookup[crn]
                merged_course = {
                    'crn': crn,
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
                    'seats': pdf_course.get('capacity') - pdf_course.get('seats'), # Changed to calculate taken seats
                    # 'seats': pdf_course.get('seats'),
                    'capacity': pdf_course.get('capacity')
                }
                merged_courses.append(merged_course)
            else:
                unmatched_crns.append(crn)

        # Log statistics
        logger.info(f"Successfully merged {len(merged_courses)} courses")
        if unmatched_crns:
            logger.warning(f"Found {len(unmatched_crns)} unmatched CRNs from Timetable")
            logger.debug(f"Unmatched CRNs: {unmatched_crns}")

        self.merged_data = merged_courses
        return merged_courses

    def save_to_csv(self, output_path: str):
        """
        Save merged data to CSV file
        Args:
            output_path: Path to save the CSV file
        """
        if not self.merged_data:
            logger.warning("No merged data available to save")
            return

        df = pd.DataFrame(self.merged_data)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved merged data to {output_path}")

    def get_statistics(self) -> Dict:
        """
        Get statistics about the merged data
        Returns:
            Dictionary containing various statistics about the data
        """
        stats = {
            'total_pdf_courses': len(self.pdf_data),
            'total_timetable_courses': len(self.timetable_data),
            'total_merged_courses': len(self.merged_data),
            'match_rate': len(self.merged_data) / len(self.pdf_data) if self.pdf_data else 0,
            # 'match_rate': len(self.merged_data) / len(self.timetable_data) if self.timetable_data else 0,
        }
        return stats
