from markitdown import MarkItDown
import re
import json

# Define course exclusion keywords
EXCLUDED_CATEGORIES = [
    "Independent Study", "Seminar", "Research and Thesis",
    "Research and Dissertation", "Project and Report", "Final Examination"
]

# Regex to identify 5000+ level courses
GRAD_COURSE_REGEX = r"CEE-(5\d{3,})"  # Matches CEE-5000+ courses


def parse_graduate_courses(markdown_obj):
    """
    Parses graduate-level courses from a MarkItDown object.
    """
    text = markdown_obj.text_content  # Get text content
    lines = text.splitlines()  # Split into lines

    graduate_courses = []
    current_course = {}

    for line in lines:
        # Check for a course code at the start of a new block
        match = re.search(GRAD_COURSE_REGEX, line)
        if match:
            # Save the previous course if it qualifies
            if current_course and not any(
                cat in current_course.get("Title", "") for cat in EXCLUDED_CATEGORIES
            ):
                graduate_courses.append(current_course)

            # Start a new course block
            current_course = {"Course Code": match.group(), "Raw Data": line.strip()}

        # Parse relevant fields
        if "Title" not in current_course and "Title" in line:
            current_course["Title"] = line.strip()
        elif "Cr" in line:  # Credit hours
            current_course["Credits"] = re.search(r"(\d+)", line).group()
        elif "Instructor" in line:
            current_course["Instructor"] = line.strip()
        elif "Days" in line:
            current_course["Schedule"] = line.strip()

    # Add the last parsed course
    if current_course and not any(
        cat in current_course.get("Title", "") for cat in EXCLUDED_CATEGORIES
    ):
        graduate_courses.append(current_course)

    return graduate_courses


if __name__ == "__main__":
    pdf_file = "/Users/mitchellgerhardt/Desktop/Fall2024_AOE.pdf"

    markitdown = MarkItDown()
    converted = markitdown.convert(pdf_file)

    courses = parse_graduate_courses(converted)

    print(courses)
