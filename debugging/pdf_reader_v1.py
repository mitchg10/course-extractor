import re
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum, auto


@dataclass
class AdditionalTime:
    days: str
    begin_time: str
    end_time: str
    location: str


@dataclass
class Course:
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
    begin_time: str
    end_time: str
    location: str
    exam_code: str
    additional_times: List[AdditionalTime]
    comments: List[str]


class ParserState(Enum):
    SEEKING_COURSE = auto()
    COLLECTING_COURSE_DATA = auto()
    COLLECTING_ADDITIONAL_TIMES = auto()
    COLLECTING_COMMENTS = auto()


class CourseParser:
    def __init__(self):
        self.current_course_data: Dict[str, str] = {}
        self.current_comments: List[str] = []
        self.current_additional_times: List[AdditionalTime] = []
        self.state = ParserState.SEEKING_COURSE
        self.courses: List[Course] = []

    def _is_course_start(self, line: str) -> bool:
        # Matches lines starting with 5 digits (CRN)
        return bool(re.match(r'^\d{5}\s+[A-Z]{2,4}-', line))

    def _is_additional_time(self, line: str) -> bool:
        return line.strip().startswith('* Additional Times *')

    def _is_comment(self, line: str) -> bool:
        return line.strip().startswith('Comments for CRN')

    def _parse_main_course_line(self, line: str) -> Dict[str, str]:
        # Complex regex to match all fields in the main course line
        pattern = r"""
            (\d{5})\s+                     # CRN
            ([A-Z]{2,4}-\d{4})\s+          # Course code
            (.+?)\s+                       # Title
            ([A-Z]|ONLINE\s*-\s*[A-Z]+)\s+ # Schedule type
            (.+?)\s+                       # Modality
            (\d+(?:\s*TO\s*\d+)?)\s+       # Credit hours
            ((?:Full(?:\s*-?\d+)?|\d+))\s+ # Seats
            (\d+)\s+                       # Capacity
            (.+?)\s+                       # Instructor
            (\(ARR\)|[MTWRF]+)\s+          # Days
            ((?:\d{1,2}:\d{2}(?:AM|PM)?|-+))\s+ # Begin time
            ((?:\d{1,2}:\d{2}(?:AM|PM)?|-+))\s+ # End time
            (.+?)\s+                       # Location
            (\d+[TMX])                     # Exam code
        """
        match = re.match(pattern, line.strip(), re.VERBOSE)
        if match:
            fields = ['crn', 'course_code', 'title', 'schedule_type', 'modality',
                      'credit_hours', 'seats', 'capacity', 'instructor', 'days',
                      'begin_time', 'end_time', 'location', 'exam_code']
            return dict(zip(fields, match.groups()))
        return {}

    def _parse_additional_time(self, line: str) -> Optional[AdditionalTime]:
        pattern = r'([MTWRF]+)\s+(\d{1,2}:\d{2}(?:AM|PM)?)\s+(\d{1,2}:\d{2}(?:AM|PM)?)\s+(.+)'
        match = re.match(pattern, line.strip())
        if match:
            return AdditionalTime(*match.groups())
        return None

    def parse_line(self, line: str):
        if self._is_course_start(line):
            # Complete previous course if exists
            if self.current_course_data:
                self._complete_current_course()

            # Start new course
            self.current_course_data = self._parse_main_course_line(line)
            self.state = ParserState.COLLECTING_COURSE_DATA

        elif self._is_additional_time(line):
            self.state = ParserState.COLLECTING_ADDITIONAL_TIMES

        elif self._is_comment(line):
            self.state = ParserState.COLLECTING_COMMENTS

        else:
            # Handle ongoing collection based on state
            if self.state == ParserState.COLLECTING_ADDITIONAL_TIMES:
                additional_time = self._parse_additional_time(line)
                if additional_time:
                    self.current_additional_times.append(additional_time)

            elif self.state == ParserState.COLLECTING_COMMENTS:
                if line.strip():
                    self.current_comments.append(line.strip())

    def _complete_current_course(self):
        if self.current_course_data:
            course = Course(
                **self.current_course_data,
                additional_times=self.current_additional_times.copy(),
                comments=self.current_comments.copy()
            )
            self.courses.append(course)

            # Reset collectors
            self.current_course_data = {}
            self.current_additional_times = []
            self.current_comments = []
            self.state = ParserState.SEEKING_COURSE

    def parse_file(self, filename: str) -> List[Course]:
        with open(filename, 'r') as f:
            for line in f:
                self.parse_line(line)

        # Complete final course if exists
        if self.current_course_data:
            self._complete_current_course()

        return self.courses


def parse_timetable(filename: str) -> List[Course]:
    parser = CourseParser()
    return parser.parse_file(filename)

# Example usage
if __name__ == "__main__":
    courses = parse_timetable("timetable.pdf")
for course in courses:
    print(f"CRN: {course.crn}")
    print(f"Title: {course.title}")
    if course.additional_times:
        print("Additional Times:")
        for time in course.additional_times:
            print(f"  {time.days} {time.begin_time}-{time.end_time} {time.location}")
    if course.comments:
        print("Comments:")
        for comment in course.comments:
            print(f"  {comment}")
    print()
