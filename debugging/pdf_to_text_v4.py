import pymupdf
import statistics
import logging
from datetime import datetime
# from pyvt import Timetable

import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from pyvt import Timetable
from CourseDataMerger import CourseDataMerger

EXPECTED_HEADERS = ["CRN", "Course", "Title", "Schedule Type", "Modality", "Cr Hrs", "Seats", "Capacity", "Instructor", "Days", "Begin", "End", "Location", "on"]
ROW_GAP_THRESHOLD = 10.0   # Vertical gap threshold between rows. Adjust as needed.
COLUMN_TOLERANCES = {
    "CRN": 5.0,
    "Course": 5.0,
    "Title": 15.0,
    "Schedule Type": 8.0,
    "Modality": 15.0,
    "Cr Hrs": 5.0,
    "Seats": 5.0,
    "Capacity": 8.0,
    "Instructor": 15.0,
    "Days": 5.0,
    "Begin": 8.0,
    "End": 8.0,
    "Location": 10.0,
    "on": 5.0,
}

def fetch_from_timetable(subject_code, term_year=None):
    # Create a timetable object
    timetable = Timetable()

    # Print all possible subjects
    subjects = timetable.subject_lookup(subject_code=subject_code, term_year=term_year, open_only=False)

    # Print the first 5 sections in the subjects
    # for i in range(5):
    #     subjects[i].print_info()

    return subjects

def process_pdf(pdf_path):
    """
    Process all pages in the PDF and extract course information.
    Headers are only on the first page, so we'll use those column boundaries for all pages.

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        list: List of validated course dictionaries
    """
    # Open PDF file
    doc = pymupdf.open(pdf_path)
    all_courses = []

    # Get headers from first page only
    first_page = doc[0]
    first_page_words = first_page.get_text("words")

    if not first_page_words:
        return []

    # Find header line and get column boundaries
    header_words = find_header_lines(first_page_words, EXPECTED_HEADERS)
    if not header_words:
        return []

    header_y_bottom = max(hw['y1'] for hw in header_words)
    column_boundaries = get_column_boundaries(header_words)

    # Process each page using the column boundaries from first page
    for page_num in range(len(doc)):
        print(f"Processing page {page_num + 1} of {len(doc)}")
        page = doc[page_num]
        words = page.get_text("words")

        # Skip empty pages
        if not words:
            continue

        # For first page, use the header_y_bottom we found
        # For other pages, we can start from top of page (or use a small offset)
        page_start_y = header_y_bottom if page_num == 0 else 0

        words_in_columns = assign_words_to_columns(words, column_boundaries, page_start_y)
        rows = cluster_words_into_rows(words_in_columns)

        # Extract course info from this page
        page_courses = extract_course_info(rows)
        print(f"Found {len(page_courses)} courses on page {page_num + 1}")
        all_courses.extend(page_courses)

    doc.close()

    # Validate all courses
    print("=== Validation Phase ===")
    print(f"Total courses before validation: {len(all_courses)}")

    validated_courses = []
    for course in all_courses:
        # Remove temporary tracking fields
        if 'row_y0' in course:
            del course['row_y0']
        page_num = course.pop('page', None)

        if all(key in course for key in ['crn', 'seats', 'capacity']):
            if course['capacity'] >= 0:
                if 0 <= course['seats'] <= course['capacity']:
                    validated_courses.append(course)
               

    print(f"Final validated courses: {len(validated_courses)}")

    return validated_courses


def find_header_lines(words, expected_headers):
    """
    Find the lines that contain all (or most) of the expected_headers.
    Returns a list of header words (dicts) if found, else None.
    """
    # Group words by their vertical line (y0)
    lines = {}
    for w in words:
        x0, y0, x1, y1, text, block_no, line_no, word_no = w
        line_key = round(y0, 1)  # rounding to 1 decimal for stability
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append({
            'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'text': text
        })

    # Try to find lines containing all or most of the headers
    header_lines = []
    for y_line, wds in sorted(lines.items()):
        line_texts = [wd['text'].lower() for wd in wds]
        matches = sum(1 for h in expected_headers if h.lower() in line_texts)
        # If the line contains a majority of expected headers, assume it's part of the header
        if matches > len(expected_headers) * 0.5:
            header_lines.append(wds)
        # Stop if we have enough lines to cover the header
        if len(header_lines) >= 5:
            break

    if not header_lines:
        return None

    # Flatten the list of header lines and sort by x0
    header_words = [word for line in header_lines for word in line]
    return sorted(header_words, key=lambda x: x['x0'])


def get_column_boundaries(header_words):
    """
    Determine column boundaries based on the header words.
    Returns a list of (column_name, min_x, max_x) tuples.
    """
    # Match header_words to expected headers in sorted order
    # We assume that the headers appear in roughly the same order as expected_headers.
    # A simple approach: find each header from expected_headers in header_words by textual match.
    found_columns = []
    used_indices = set()
    for expected in EXPECTED_HEADERS:
        # Find best match in header_words
        candidates = [(i, hw) for i, hw in enumerate(header_words) if expected.lower() in hw['text'].lower() and i not in used_indices]
        if candidates:
            # Choose the first match (or best match if multiple)
            i, hw = candidates[0]
            used_indices.add(i)
            found_columns.append((expected, hw['x0'], hw['x1']))
        else:
            # If a header is not found, append a placeholder
            # You may need a fallback strategy if headers don't match exactly.
            found_columns.append((expected, None, None))

    # Now that we have a list of (header, x0, x1), fill in missing columns by approximating boundaries.
    # Sort by x0
    found_columns = [fc for fc in found_columns if fc[1] is not None]
    found_columns.sort(key=lambda c: c[1])

    # Determine boundaries between columns:
    # If we have N columns, we have at most N boundaries (left edge of first col to right edge of last col).
    # We'll assume that the "max_x" of one column to the "min_x" of the next column sets boundaries.
    boundaries = []
    for i, (col_name, x_start, x_end) in enumerate(found_columns):
        tolerance = COLUMN_TOLERANCES.get(col_name, 5.0)  # Use the specific tolerance for the column
        if i == 0:
            # Left boundary of first column
            left_bound = x_start - tolerance
        else:
            # Use midpoint between this column's start and previous column's end as boundary
            prev_col = boundaries[-1]
            left_bound = (prev_col[2] + x_start) / 2.0
        # For the last column, we extend to a large number
        if i == len(found_columns) - 1:
            right_bound = x_end + 1000
        else:
            # Temporarily, just set right_bound to x_end; we'll refine after loop
            right_bound = x_end + tolerance
        boundaries.append((col_name, left_bound, right_bound))

    # Refine boundaries: now that we have them, recompute the midpoint boundaries properly
    refined = []
    for i in range(len(boundaries)):
        col_name, l, r = boundaries[i]
        if i < len(boundaries) - 1:
            # midpoint between current col's right boundary and next col's left side
            next_col_name, nl, nr = boundaries[i+1]
            new_r = (r + nl) / 2.0
            refined.append((col_name, l, new_r))
        else:
            # last column extends to large right margin
            refined.append((col_name, l, r))

    return refined


def assign_words_to_columns(words, column_boundaries, header_y_bottom):
    """
    Assign words (not header words) to the appropriate column based on x-coordinates.
    We skip the header line itself (words above header_y_bottom).
    """
    # Filter out header line words
    data_words = [w for w in words if w[1] > header_y_bottom]

    # Assign each word to a column
    row_entries = []
    for w in data_words:
        x0, y0, x1, y1, text, block_no, line_no, word_no = w
        for col_name, col_left, col_right in column_boundaries:
            if x0 >= col_left and x1 <= col_right:
                row_entries.append({
                    'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                    'text': text,
                    'col': col_name
                })
                break
    return row_entries


def cluster_words_into_rows(words_in_columns):
    """
    Cluster words by proximity in vertical direction to form rows.
    We'll sort by y0, then group words into rows based on gaps.
    """
    if not words_in_columns:
        return []

    words_in_columns.sort(key=lambda w: w['y0'])

    rows = []
    current_row = []
    last_y = None

    for w in words_in_columns:
        if last_y is None:
            current_row.append(w)
            last_y = w['y0']
        else:
            # Check gap
            gap = w['y0'] - last_y
            if gap > ROW_GAP_THRESHOLD:
                # New row
                rows.append(current_row)
                current_row = [w]
            else:
                current_row.append(w)
            last_y = w['y0']
    if current_row:
        rows.append(current_row)

    return rows


def extract_course_info(rows):
    """
    Extract and validate CRN, Seats, and Capacity information from rows data.

    Args:
        rows (list): List of row data from PDF extraction

    Returns:
        list: List of dictionaries containing validated CRN, Seats, and Capacity
    """
    course_info = []
    current_info = {}

    for row in rows:
        for word_info in row:
            text = word_info['text']
            column = word_info['col']
            y0 = word_info['y0']  # Use y0 to group related information

            # Extract CRN
            if column == 'CRN' and text.strip().isdigit() and len(text.strip()) == 5:
                if current_info.get('crn'):
                    course_info.append(current_info.copy())
                current_info = {'crn': text.strip(), 'row_y0': y0}

            # Extract Seats - only process if within same vertical position (y0) as CRN
            elif column == 'Seats' and current_info.get('row_y0'):
                # Allow small tolerance in y0 comparison (e.g., ±2 points)
                if abs(y0 - current_info['row_y0']) < 2:
                    seats_val = text.strip()
                    current_info['seats_val'] = seats_val
                    if seats_val.isdigit():
                        current_info['seats'] = int(seats_val)
                    # else if "Full #", extract the number
                    elif seats_val.startswith("Full "):
                        full_num = seats_val[5:]
                        if full_num.isdigit():
                            current_info['seats'] = int(full_num)

            # Extract Capacity - only process if within same vertical position as CRN
            elif column == 'Capacity' and current_info.get('row_y0'):
                if abs(y0 - current_info['row_y0']) < 2:
                    capacity_val = text.strip()
                    if capacity_val.isdigit():
                        current_info['capacity'] = int(capacity_val)

    # Add the last course if exists
    if current_info.get('crn'):
        course_info.append(current_info.copy())

    # Remove temporary y0 tracking
    for course in course_info:
        if 'row_y0' in course:
            del course['row_y0']

    # Validate the extracted data
    validated_courses = []
    for course in course_info:
        # Check if we have all required fields
        if all(key in course for key in ['crn', 'seats', 'seats_val', 'capacity']):
            # Verify capacity is not zero or negative
            if course['capacity'] >= 0:
                # Verify seats don't exceed capacity
                if 0 <= course['seats'] <= course['capacity']:
                    validated_courses.append(course)

    return validated_courses

if __name__ == "__main__":
    pdf_file = "/Users/mitchellgerhardt/Desktop/Spring2025_COE.pdf"

    # data = extract_table_from_pdf(pdf_file, page_number=0)

    # Timetable data
    timetable_data = fetch_from_timetable("CEE", term_year="202501") # [1, 6, 7, 9] <- Spring, Summer I, Summer II, Fall

    course_data = process_pdf(pdf_file)

    # Write to a CSV file
    with open("course_data.csv", "w", encoding="utf-8") as f:
        f.write("CRN,Seats,Seats_Val,Capacity\n")
        for course in course_data:
            f.write(f"{course['crn']},{course['seats']},{course['seats_val']},{course['capacity']}\n")

    # Create merger instance
    merger = CourseDataMerger()
    
    # Load both datasets
    merger.load_pdf_data(course_data)
    merger.load_timetable_data(timetable_data)
    
    # Merge the data
    merged_courses = merger.merge_course_data()
    
    # Save to CSV
    merger.save_to_csv("merged_course_data.csv")
    
    # Print statistics
    stats = merger.get_statistics()
    print("\nMerging Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")
