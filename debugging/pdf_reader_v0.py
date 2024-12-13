import pdfplumber
import pandas as pd
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

# Configure logging
logging.basicConfig(filename='processing.log', level=logging.INFO, format='%(message)s')


class ParserState(Enum):
    SEEKING_COURSE = auto()
    COLLECTING_COURSE = auto()
    COLLECTING_COMMENTS = auto()


@dataclass
class CourseInfo:
    crn: str
    course_code: str
    title: str
    schedule_type: str
    modality: str
    credit_hours: str
    seats: str
    capacity: str
    instructor: str
    days: str
    start_time: str
    end_time: str
    location: str
    exam_code: str
    comments: List[str]


class CourseScheduleExtractor:
    def __init__(self, pdf_directory: str):
        self.pdf_directory = Path(pdf_directory)
        self.current_course_lines: List[str] = []
        self.current_comments: List[str] = []
        self.state = ParserState.SEEKING_COURSE

    def extract_all_pdfs(self) -> Dict[str, pd.DataFrame]:
        """Extract course information from all PDFs in the directory."""
        results = {}
        for pdf_path in self.pdf_directory.glob('*.pdf'):
            department = pdf_path.stem
            df = self.process_single_pdf(pdf_path)
            results[department] = df
        return results

    def process_single_pdf(self, pdf_path: Path) -> pd.DataFrame:
        """Process a single PDF and return structured data."""
        courses = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text_lines = page.extract_text().split('\n')
                for line in text_lines:
                    course = self._process_line(line)
                    if course:
                        courses.append(course)

        return self._convert_to_dataframe(courses)

    def _process_line(self, line: str) -> Optional[CourseInfo]:
        """Process a single line and maintain state for multi-line entries."""
        line = line.strip()
        logging.info(f"Processing line: {line}")
        if not line:
            logging.info("Line is empty, returning None")
            return None

        # Check for comment lines
        if line.startswith('Comments for CRN'):
            logging.info("Line starts with 'Comments for CRN', switching state to COLLECTING_COMMENTS")
            self.state = ParserState.COLLECTING_COMMENTS
            return None

        if self.state == ParserState.COLLECTING_COMMENTS:
            if self._looks_like_course_start(line):
                logging.info("Detected start of a new course while collecting comments, switching state to COLLECTING_COURSE")
                self.state = ParserState.COLLECTING_COURSE
                self.current_course_lines = [line]
            else:
                logging.info("Collecting comment line")
                self.current_comments.append(line)
            return None

        # Handle course lines
        if self._looks_like_course_start(line):
            logging.info("Detected start of a new course")
            # If we were already collecting a course, try to parse it
            if self.current_course_lines:
                logging.info("Already collecting a course, attempting to parse current course")
                course = self._try_parse_course()
                self.current_course_lines = [line]
                return course
            else:
                logging.info("Starting to collect a new course")
                self.current_course_lines = [line]
                self.state = ParserState.COLLECTING_COURSE
                return None

        # If we're collecting a course, add this line
        if self.state == ParserState.COLLECTING_COURSE:
            logging.info("Collecting course line")
            self.current_course_lines.append(line)
            # Try to parse if we think we have a complete entry
            if self._looks_like_course_end(line):
                logging.info("Detected end of course, attempting to parse course")
                course = self._try_parse_course()
                self.current_course_lines = []
                return course

        logging.info("Line did not match any specific conditions, returning None")
        return None

    def _looks_like_course_start(self, line: str) -> bool:
        """Check if line looks like the start of a course entry."""
        pattern = r'^\d{5}\s+AOE-'
        return bool(re.match(pattern, line))

    def _looks_like_course_end(self, line: str) -> bool:
        """Check if line looks like the end of a course entry."""
        return line.endswith(('TBA 00X', 'ONLINE 00X'))

    def _try_parse_course(self) -> Optional[CourseInfo]:
        """Attempt to parse collected lines into a CourseInfo object."""
        if not self.current_course_lines:
            return None

        # Join all lines and clean up extra whitespace
        full_text = ' '.join(self.current_course_lines)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        # Pattern to match the complete course information
        pattern = r"""
            (\d{5})\s+                  # CRN
            AOE-\s*
            (\d{4})\s+                  # Course code
            (.+?)\s+                    # Title
            ([A-Z]|ONLINE\s*-\s*V[BLR])\s+ # Schedule type
            ((?:Face-to-Face|Online[:\s].*?|ARR))\s+ # Modality
            (\d+(?:\s*TO\s*\d+)?)\s+    # Credit hours
            ((?:Full|-?\d+))\s+         # Seats
            (-?\d+|\s+)\s+              # Capacity
            ([^(]+?)\s+                 # Instructor
            (\(ARR\)|[MTWRF]+)\s+       # Days
            ((?:\d{1,2}:\d{2}(?:AM|PM)?|\-+))\s+ # Start time
            ((?:\d{1,2}:\d{2}(?:AM|PM)?|\-+))\s+ # End time
            ((?:TBA|ONLINE|[^0]\S+))\s+ # Location
            (\d+[TMX])                  # Exam code
        """

        match = re.match(pattern, full_text, re.VERBOSE)
        if match:
            course = CourseInfo(*match.groups(), comments=self.current_comments.copy())
            self.current_comments = []  # Clear comments after using them
            return course

        return None

    def _convert_to_dataframe(self, courses: List[CourseInfo]) -> pd.DataFrame:
        """Convert list of CourseInfo objects to DataFrame."""
        return pd.DataFrame([vars(c) for c in courses])


# Example usage
if __name__ == "__main__":
    extractor = CourseScheduleExtractor("./data")
    department_data = extractor.extract_all_pdfs()

    # Save each department's data to CSV
    for department, df in department_data.items():
        df.to_csv(f"{department}_courses.csv", index=False)
        print(f"Processed {len(df)} courses for {department}")
