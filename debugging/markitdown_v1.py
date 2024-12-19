import re
import json
from markitdown import MarkItDown

# Regex to identify relevant course fields
CRN_REGEX = r"^\d{5}"  # Matches a CRN (e.g., 12350)
COURSE_REGEX = r"CEE-\s*\d{4}"  # Matches course codes like "CEE-5304"
CREDIT_REGEX = r"^\d+$"  # Matches credit hours
EXAM_REGEX = r"\d{2}[A-Z]{1,2}$"  # Matches exam codes (e.g., "09T")
DAYS_REGEX = r"^(M|T|W|R|F|S)$"  # Matches individual days (e.g., "T", "R")
TIME_REGEX = r"^\d{1,2}:\d{2}[APM]{2}$"  # Matches time format like "9:30AM"

EXCLUDED_CATEGORIES = [
    "Independent Study", "Seminar", "Research and Thesis",
    "Research and Dissertation", "Project and Report", "Final Examination"
]


def parse_graduate_courses(markdown_obj):
    """
    Parses graduate-level courses from a MarkItDown object.
    """
    text = markdown_obj.text_content  # Get text content
    lines = text.splitlines()  # Split into lines

    graduate_courses = []
    current_course = {}

    for line in lines:
        line = line.strip()

        # Match CRN
        if re.match(CRN_REGEX, line):
            if current_course:
                # Save the previous course if valid
                if not any(
                    cat in current_course.get("Title", "") for cat in EXCLUDED_CATEGORIES
                ):
                    graduate_courses.append(current_course)
            # Initialize a new course
            current_course = {"CRN": line}

        # Match Course Code
        elif re.search(COURSE_REGEX, line):
            current_course["Course"] = line

        # Match Title (assume it's the line following the course code)
        elif "Course" in current_course and "Title" not in current_course:
            current_course["Title"] = line

        # Match Schedule Type
        elif line in ["L", "I", "B", "R"]:  # Example schedule types
            current_course["Schedule Type"] = line

        # Match Modality
        elif "Instruction" in line:
            current_course["Modality"] = line

        # Match Credit Hours
        elif re.match(CREDIT_REGEX, line):
            current_course["Cr Hrs"] = int(line)

        # Match Seats and Capacity
        elif "Seats" not in current_course and line.isdigit():
            current_course["Seats"] = int(line)
        elif "Seats" in current_course and "Capacity" not in current_course and line.isdigit():
            current_course["Capacity"] = int(line)

        # Match Instructor
        elif "Instructor" not in current_course and re.search(r"[A-Za-z\s]+", line):
            current_course["Instructor"] = line

        # Match Days
        elif all(day in line.split() for day in ["M", "T", "W", "R", "F", "S"]):
            current_course["Days"] = line.split()

        # Match Time and Location
        elif re.match(TIME_REGEX, line):
            if "Begin" not in current_course:
                current_course["Begin"] = [line]
            elif "End" not in current_course:
                current_course["End"] = [line]
        elif "PAT" in line or "WLH" in line or "SURGE" in line:  # Example locations
            current_course["Location"] = line

        # Match Exam Code
        elif re.match(EXAM_REGEX, line):
            current_course["Exam"] = line

        # Match Comments
        elif "Comments for CRN" in line:
            comment_index = lines.index(line) + 1
            comments = []
            while comment_index < len(lines) and lines[comment_index].strip():
                comments.append(lines[comment_index].strip())
                comment_index += 1
            current_course["Comments"] = " ".join(comments)

    # Add the last parsed course if valid
    if current_course and not any(
        cat in current_course.get("Title", "") for cat in EXCLUDED_CATEGORIES
    ):
        graduate_courses.append(current_course)

    return graduate_courses


def main(input_file, output_file):
    """
    Main function to parse the markdown file and save graduate courses to JSON.
    """
    markdown_obj = MarkItDown() 
    converted = markdown_obj.convert(input_file)
    graduate_data = parse_graduate_courses(converted)

    # Save the structured graduate course data to a JSON file
    with open(output_file, "w") as f:
        json.dump(graduate_data, f, indent=2)

    print(f"Extracted {len(graduate_data)} graduate courses. Saved to {output_file}.")


# Input and output file paths
input_file = "/Users/mitchellgerhardt/Desktop/Spring2025_COE.pdf"  # Replace with your actual file path
output_file = "graduate_courses.json"

if __name__ == "__main__":
    main(input_file, output_file)
