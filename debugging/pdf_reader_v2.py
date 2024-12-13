from pathlib import Path
import re
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum, auto
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class AdditionalTime:
    days: str
    begin_time: str
    end_time: str
    location: str


@dataclass
class Course:
    crn: str
    course_code: str  # e.g., AOE-2024
    title: str
    schedule_type: str  # L, B, R, etc.
    modality: str  # Face-to-Face, Online, etc.
    credit_hours: str  # Can be "3" or "1 TO 19"
    seats: str  # Can be number or "Full -1"
    capacity: str
    instructor: str
    days: str  # Can be specific days or "(ARR)"
    begin_time: str  # Can be time or "-----"
    end_time: str   # Can be time or "-----"
    location: str   # Can be room or "TBA"
    exam_code: str  # e.g., "09M", "00X"
    additional_times: List[AdditionalTime]
    comments: List[str]


class ParserState(Enum):
    SEEKING_COURSE = auto()
    COLLECTING_COMMENTS = auto()


class CourseParser:
    def __init__(self, max_courses: Optional[int] = None):
        self.current_course: Optional[Course] = None
        self.current_comments: List[str] = []
        self.state = ParserState.SEEKING_COURSE
        self.courses: List[Course] = []
        self.max_courses = max_courses
        logger.info(f"Initialized parser with max_courses={max_courses}")
        
    def _parse_course_line(self, line: str) -> Optional[Dict[str, str]]:
        logger.debug(f"Attempting to parse line: {line[:100]}...")  # First 100 chars for brevity
        # Updated pattern to match the actual format
        pattern = r"""
            (\d{5})\s+                     # CRN
            ([A-Z]{2,4}-\s*\d{4})\s+       # Course code (handle possible space)
            ([^RLBI\s][^RLBI]*?)\s+        # Title (up to schedule type)
            ([RLBI]|ONLINE\s*-\s*[VI][RLI]?)\s+ # Schedule type
            ([^0-9]+?)\s+                  # Modality
            (\d+(?:\s*TO\s*\d+)?)\s+       # Credit hours
            (Full(?:\s*-?\d+)?|\d+)\s+     # Seats
            (-?\d+)\s+                     # Capacity
            (.+?)\s+                       # Instructor
            (\(ARR\)|[MTWRF]+)\s+          # Days
            ((?:\d{1,2}:\d{2}(?:AM|PM)?|-+))\s+ # Begin time
            ((?:\d{1,2}:\d{2}(?:AM|PM)?|-+))\s+ # End time
            ([^0-9]+?)\s+                  # Location
            (\d+[MTX])                     # Exam code
        """
        match = re.match(pattern, line.strip(), re.VERBOSE)
        if not match:
            logger.debug("Line did not match course pattern")
            return None
            
        fields = ['crn', 'course_code', 'title', 'schedule_type', 'modality',
                 'credit_hours', 'seats', 'capacity', 'instructor', 'days',
                 'begin_time', 'end_time', 'location', 'exam_code']
        
        data = dict(zip(fields, match.groups()))
        
        # Clean up the data
        data['course_code'] = data['course_code'].replace(' ', '')
        data['title'] = data['title'].strip()
        data['modality'] = data['modality'].strip()
        data['location'] = data['location'].strip()
        
        logger.debug(f"Successfully parsed course: {data['crn']} {data['course_code']}")
        return data

    def parse_line(self, line: str):
        # Skip empty lines and metadata
        if not line.strip() or "Metadata:" in line or "Return to selection" in line:
            return

        # Check if we've reached the maximum number of courses
        if self.max_courses and len(self.courses) >= self.max_courses:
            return

        # Check if it's a comment line
        if line.strip().startswith('Comments for CRN'):
            self.state = ParserState.COLLECTING_COMMENTS
            if self.current_course:
                crn_match = re.search(r'Comments for CRN (\d{5}):', line)
                if crn_match and crn_match.group(1) == self.current_course.crn:
                    logger.debug(f"Found comments for CRN {crn_match.group(1)}")
                    return
            
        # If we're collecting comments and it's not a new course
        if self.state == ParserState.COLLECTING_COMMENTS and not self._is_course_start(line):
            comment_line = line.strip()
            if comment_line and not comment_line.startswith('* Additional Times *'):
                self.current_comments.append(comment_line)
                logger.debug(f"Added comment: {comment_line[:50]}...")  # First 50 chars
            return

        # Check if it's a new course
        if self._is_course_start(line):
            # Complete previous course if exists
            if self.current_course:
                self._complete_current_course()

            # Parse new course
            course_data = self._parse_course_line(line)
            if course_data:
                self.current_course = Course(
                    **course_data,
                    additional_times=[],
                    comments=[]
                )
                logger.info(f"Started parsing new course: {course_data['crn']} {course_data['course_code']}")
                self.state = ParserState.SEEKING_COURSE

    def _is_course_start(self, line: str) -> bool:
        return bool(re.match(r'^\d{5}\s+[A-Z]{2,4}-\s*\d{4}', line))

    def _complete_current_course(self):
        if self.current_course:
            if self.current_comments:
                self.current_course.comments = self.current_comments.copy()
                logger.debug(f"Added {len(self.current_comments)} comments to course {self.current_course.crn}")
            self.courses.append(self.current_course)
            logger.info(f"Completed parsing course {self.current_course.crn} {self.current_course.course_code}")
            self.current_course = None
            self.current_comments = []
            self.state = ParserState.SEEKING_COURSE

    def parse_text(self, text: str) -> List[Course]:
        logger.info("Starting to parse text")
        for line in text.split('\n'):
            self.parse_line(line)
            if self.max_courses and len(self.courses) >= self.max_courses:
                logger.info(f"Reached maximum number of courses ({self.max_courses})")
                break

        # Complete final course if exists
        if self.current_course:
            self._complete_current_course()

        logger.info(f"Completed parsing. Found {len(self.courses)} courses")
        return self.courses


def parse_timetable(text: str) -> List[Course]:
    """Parse timetable text and return list of courses."""
    parser = CourseParser(max_courses=5)
    return parser.parse_text(text)

# Helper function to print course details
def print_course_details(course: Course):
    print(f"\nCRN: {course.crn}")
    print(f"Course: {course.course_code} - {course.title}")
    print(f"Schedule: {course.days} {course.begin_time}-{course.end_time}")
    print(f"Location: {course.location}")
    print(f"Instructor: {course.instructor}")
    print(f"Modality: {course.modality}")
    print(f"Credits: {course.credit_hours}")
    print(f"Enrollment: {course.seats}/{course.capacity}")
    if course.comments:
        print("Comments:")
        for comment in course.comments:
            print(f"  {comment}")


# Helper function to print course details
def print_course_details(course: Course):
    print(f"\nCRN: {course.crn}")
    print(f"Course: {course.course_code} - {course.title}")
    print(f"Schedule: {course.days} {course.begin_time}-{course.end_time}")
    print(f"Location: {course.location}")
    print(f"Instructor: {course.instructor}")
    print(f"Modality: {course.modality}")
    print(f"Credits: {course.credit_hours}")
    print(f"Enrollment: {course.seats}/{course.capacity}")
    if course.comments:
        print("Comments:")
        for comment in course.comments:
            print(f"  {comment}")

if __name__ == "__main__":
    # Example usage with a text file
    file_path = Path("../data/raw_text/raw_text_20241213_175758.txt")
    with open(file_path, "r") as file:
        text = file.read()
        logger.info(f"Read {len(text)} characters from file")
        
    courses = parse_timetable(text)

    # Print details of first few courses
    print(f"\nFound {len(courses)} courses:")   
    for course in courses[:3]:
        print_course_details(course)