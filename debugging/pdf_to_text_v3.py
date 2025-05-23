import pymupdf
import statistics
from markitdown import MarkItDown
import logging
from datetime import datetime

# Adjust these to fit your PDF
expected_headers = ["CRN", "Course", "Title", "Schedule Type", "Modality", "Cr Hrs", "Seats", "Capacity", "Instructor", "Days", "Begin", "End", "Location", "on"]
ROW_GAP_THRESHOLD = 10.0   # Vertical gap threshold between rows. Adjust as needed.
# COLUMN_TOLERANCE = 5.0   # Horizontal tolerance for assigning words to columns.
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


def setup_logger(name):
    """Set up logger with file and console handlers."""
    # Create logs directory if it doesn't exist
    import os
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create logger with name
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers if any
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create file handler
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    fh = logging.FileHandler(f'logs/course_extraction_{timestamp}.log')
    fh.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(fh)

    return logger


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
    for expected in expected_headers:
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

    print("Found columns:", found_columns)

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
    # logger = setup_logger('course_extraction')

    # logger.info("=== Starting Data Extraction ===")
    # logger.info(f"Number of rows to process: {len(rows)}")

    course_info = []
    current_info = {}

    # Debug first few rows
    # logger.debug("\nFirst few rows structure:")
    # for row in rows[:3]:
        # logger.debug(f"Row content: {row}")

    for row in rows:
        # Log the current row being processed
        # logger.debug(f"Processing row: {row}")

        for word_info in row:
            text = word_info['text']
            column = word_info['col']
            y0 = word_info['y0']  # Use y0 to group related information
            
            # Extract CRN
            if column == 'CRN' and text.strip().isdigit() and len(text.strip()) == 5:
                if current_info.get('crn'):
                    # logger.debug(f"Saving previous course info: {current_info}")
                    course_info.append(current_info.copy())
                current_info = {'crn': text.strip(), 'row_y0': y0}
                # logger.debug(f"Started new course with CRN: {current_info['crn']}")
            
            # Extract Seats - only process if within same vertical position (y0) as CRN
            elif column == 'Seats' and current_info.get('row_y0'):
                # Allow small tolerance in y0 comparison (e.g., ±2 points)
                if abs(y0 - current_info['row_y0']) < 2:
                    seats_val = text.strip()
                    if seats_val.isdigit():
                        current_info['seats'] = int(seats_val)
                        # logger.debug(f"Added seats: {current_info['seats']}")
            
            # Extract Capacity - only process if within same vertical position as CRN
            elif column == 'Capacity' and current_info.get('row_y0'):
                if abs(y0 - current_info['row_y0']) < 2:
                    capacity_val = text.strip()
                    if capacity_val.isdigit():
                        current_info['capacity'] = int(capacity_val)
                        # logger.debug(f"Added capacity: {current_info['capacity']}")

    # Add the last course if exists
    if current_info.get('crn'):
        # logger.debug(f"Adding final course info: {current_info}")
        course_info.append(current_info.copy())
    
    # Remove temporary y0 tracking
    for course in course_info:
        if 'row_y0' in course:
            del course['row_y0']

    # logger.info("=== Validation Phase ===")
    # logger.info(f"Courses before validation: {len(course_info)}")

    # Validate the extracted data
    validated_courses = []
    for course in course_info:
        # logger.debug(f"Validating course: {course}")
        # Check if we have all required fields
        if all(key in course for key in ['crn', 'seats', 'capacity']):
            # logger.debug("All required fields present")
            # Verify capacity is not zero or negative
            if course['capacity'] >= 0:
                # logger.debug("Capacity is valid")
                # Verify seats don't exceed capacity
                if 0 <= course['seats'] <= course['capacity']:
                    # logger.debug("Seats within valid range")
                    validated_courses.append(course)
                    # logger.debug("Course validated and added")
                # else:
                    # logger.warning(f"Invalid seats/capacity relationship: seats={course['seats']}, capacity={course['capacity']}")
            # else:
                # logger.warning(f"Invalid capacity: {course['capacity']}")
        # else:
            # logger.warning(f"Missing required fields. Present fields: {course.keys()}")

    # logger.info(f"Final validated courses: {len(validated_courses)}")
    # for course in validated_courses:
        # logger.info(f"Validated course - CRN: {course['crn']}, Seats: {course['seats']}, Capacity: {course['capacity']}")

    return validated_courses


def extract_table_from_pdf(pdf_path, page_number=0):
    doc = pymupdf.open(pdf_path)  # ! Make this all pages
    page = doc[page_number]
    words = page.get_text("words")
    if not words:
        return []

    # 1. Find header line
    header_words = find_header_lines(words, expected_headers)
    if not header_words:
        print("Header line not found. Check your expected_headers or PDF layout.")
        return []

    # Determine the bottom y of the header line to separate data rows from headers
    header_y_bottom = max(hw['y1'] for hw in header_words)

    # 2. Get column boundaries
    column_boundaries = get_column_boundaries(header_words)

    # 3. Assign words to columns
    words_in_columns = assign_words_to_columns(words, column_boundaries, header_y_bottom)

    # 4. Cluster words into rows
    rows = cluster_words_into_rows(words_in_columns)

    logger = logging.getLogger('course_extraction')
    logger.info("=== Initial Rows Data ===")
    logger.info(f"Type of rows_data: {type(rows)}")
    logger.info(f"Length of rows_data: {len(rows)}")

    # 5. Get necessary information from rows
    course_data = extract_course_info(rows)

    logger.info("=== Final Results ===")
    logger.info(f"Number of valid courses extracted: {len(course_data)}")

    # 5. Construct row dictionaries
    # row_dicts = construct_row_dicts(rows, column_boundaries)

    # return row_dicts

    # Write the header line to a file and the column boundaries

    with open("words_in_columns.txt", "w", encoding="utf-8") as f:
        for w in words_in_columns:
            f.write(f"{w['text']} ({w['col']})\n")

    with open("rows.txt", "w", encoding="utf-8") as f:
        for r in rows:
            for w in r:
                f.write(f"{w['text']} ({w['col']})\n")
            f.write("\n")

    with open("course_info.txt", "w", encoding="utf-8") as f:
        for course in course_data:
            f.write(f"CRN: {course['crn']}, Seats: {course['seats']}, Capacity: {course['capacity']}\n")

    doc.close()

    # return row_dicts
    return []


if __name__ == "__main__":
    pdf_file = "/Users/mitchellgerhardt/Desktop/Spring2025_COE.pdf"

    # Setup logger
    setup_logger('course_extraction')

    data = extract_table_from_pdf(pdf_file, page_number=0)

    # Print or save to CSV/JSON
    # import json
    # print(json.dumps(data, indent=2))

    # To save as CSV if needed:
    # import csv
    # if data:
    #     fieldnames = data[0].keys()
    #     with open("output.csv", "w", newline="", encoding="utf-8") as csvfile:
    #         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #         writer.writeheader()
    #         writer.writerows(data)
