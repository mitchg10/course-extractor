import pymupdf  # PyMuPDF
import re
import json


def extract_table(pdf_path, output_json):
    doc = pymupdf.open(pdf_path)
    table_data = []

    for page_num, page in enumerate(doc):
        words = page.get_text("words")
        # Sort words top-to-bottom (y), then left-to-right (x)
        words.sort(key=lambda w: (round(w[1], 2), round(w[0], 2)))

        # Convert to a simpler structure: [(x0, y0, word), ...]
        # We'll ignore x1,y1 for simplicity here
        simple_words = [(w[0], w[1], w[4]) for w in words]

        # Identify table headers
        # For example, we know the first row might contain "CRN", "Course", "Title", etc.
        # We'll look for a line containing these known headers.
        headers = ["CRN", "Course", "Title", "Schedule", "Type", "Modality", "Cr", "Hrs", "Seats", "Capacity", "Instructor", "Days", "Begin", "End", "Location", "Exam"]
        header_line, header_y = find_header_line(simple_words, headers)

        if not header_line:
            # If no header line on this page, continue or handle differently
            continue

        # Determine column boundaries using header_line words
        col_positions = get_column_boundaries(header_line)
        # col_positions is a list of x-coordinates that separate columns

        # Extract rows below the header
        rows = group_words_into_rows(simple_words, header_y)
        for row in rows:
            # Assign words to columns based on col_positions
            row_data = words_to_columns(row, col_positions, headers)
            if row_data:
                table_data.append(row_data)

    doc.close()

    # Save table_data to JSON for inspection
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(table_data, f, ensure_ascii=False, indent=2)


def find_header_line(words, header_keywords):
    """Find the line that contains the header keywords."""
    # Group words by line (y coordinate)
    lines = {}
    y_threshold = 2.0
    for x, y, w in words:
        line_key = round(y, 1)
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append((x, w))
    # For each line, check if it contains a subset of header keywords
    for y, line_words in lines.items():
        line_text = " ".join(w for x, w in sorted(line_words, key=lambda i: i[0]))
        # Check how many headers appear in this line
        found_count = sum(h in line_text for h in header_keywords)
        # Heuristic: if we find a reasonable number of header terms, assume this is the header line
        if found_count > len(header_keywords)*0.3:
            # Return this line sorted by x
            return sorted(line_words, key=lambda i: i[0]), y
    return None, None


def get_column_boundaries(header_line):
    # header_line is a list of (x, word) for the header
    # The x positions of header words can define column boundaries.
    # For simplicity, let's say each header word defines a column start.
    # If columns need better definition, you can also consider spacing.
    # We'll just take each header word's x as a column boundary start.
    col_positions = [x for x, w in header_line]
    # Sort them
    col_positions.sort()
    return col_positions


def group_words_into_rows(words, header_y):
    """Group words into rows, ignoring everything above the header_y."""
    # We know header_y: everything below it is data.
    # Group by y coordinate again
    lines = {}
    y_threshold = 2.0
    for x, y, w in words:
        if y <= header_y:
            continue
        line_key = round(y, 1)
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append((x, w))

    # Return lines as lists of (x, word) sorted by x
    row_list = []
    for y, line_words in lines.items():
        line_words.sort(key=lambda i: i[0])
        row_list.append(line_words)
    # Sort rows by y if needed - they are keys anyway
    return row_list


def words_to_columns(line_words, col_positions, headers):
    """Assign words in line_words to columns based on col_positions."""
    # col_positions define the start of each column.
    # For simplicity, assume that the column boundaries are midpoints between these positions.
    # Let's say col_boundaries is a list of column end boundaries (midpoints between col_positions)
    col_boundaries = []
    for i in range(len(col_positions)-1):
        midpoint = (col_positions[i] + col_positions[i+1]) / 2
        col_boundaries.append(midpoint)

    # Now assign each word to a column
    # If a word's x < first midpoint, col=0
    # Else find where x fits between midpoints
    n_cols = len(col_positions)
    columns = [[] for _ in range(n_cols)]

    for x, w in line_words:
        col_index = 0
        for boundary in col_boundaries:
            if x > boundary:
                col_index += 1
            else:
                break
        # Add word to this column
        columns[col_index].append(w)

    # Join column words
    col_text = [" ".join(c).strip() for c in columns]

    # Create dict keyed by header if headers and col_text align
    # You might need to align the number of headers with the number of columns found
    if len(col_text) != len(headers):
        # If mismatch, you can handle error or try a heuristic
        # We'll just skip rows that don't match column count
        return None

    row_data = dict(zip(headers, col_text))
    return row_data


if __name__ == "__main__":
    pdf_path = "path/to/Fall2024_AOE.pdf"
    output_json = "output_table.json"
    extract_table(pdf_path, output_json)
