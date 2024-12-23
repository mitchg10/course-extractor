from pathlib import Path
import pymupdf
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pyvt import Timetable
from .course_merger import CourseDataMerger

# Constants from pdf_to_text_v4.py
EXPECTED_HEADERS = ["CRN", "Course", "Title", "Schedule Type", "Modality", "Cr Hrs",
                    "Seats", "Capacity", "Instructor", "Days", "Begin", "End", "Location", "on"]
ROW_GAP_THRESHOLD = 10.0
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


class PDFProcessor:
    def __init__(self):
        self.logger = self._setup_logger()
        self.merger = CourseDataMerger()

    def _setup_logger(self) -> logging.Logger:
        """Set up logger with file and console handlers."""
        logger = logging.getLogger('pdf_processor')
        logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)

        # Remove existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()

        # Create file handler
        timestamp = datetime.now().strftime('%Y%m%d_%H_%M_%S')
        fh = logging.FileHandler(f'logs/{timestamp}_pdf_processor.log')
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

    def process_pdf(self, pdf_path: Path, subject_code: str, term_year: str) -> Dict:
        """
        Process a single PDF file and extract course information.

        Args:
            pdf_path (Path): Path to the PDF file
            subject_code (str): Department code (e.g., "AOE")
            term_year (str): Term year code (e.g., "202409")

        Returns:
            Dict: Processing results including status and extracted data
        """
        try:
            # Extract course data from PDF
            self.logger.info(f"Processing PDF: {pdf_path}")
            course_data = self._extract_from_pdf(pdf_path)

            if not course_data:
                raise ValueError("No valid course data extracted from PDF")

            # Fetch timetable data
            self.logger.info(f"Fetching timetable data for {subject_code}")
            timetable_data = self._fetch_timetable_data(subject_code, term_year)

            # Merge data using CourseDataMerger
            self.merger.load_pdf_data(course_data)
            self.merger.load_timetable_data(timetable_data)
            merged_courses = self.merger.merge_course_data()

            # Save to CSV
            output_path = self._save_to_csv(merged_courses, pdf_path.stem)

            # Get statistics
            stats = self.merger.get_statistics()

            return {
                "status": "success",
                "pdf_courses": len(course_data),
                "merged_courses": len(merged_courses),
                "output_path": str(output_path),
                "statistics": stats
            }

        except Exception as e:
            self.logger.error(f"Error processing {pdf_path}: {str(e)}", exc_info=True)
            raise

    def _extract_from_pdf(self, pdf_path: Path) -> List[Dict]:
        """Extract course information from PDF file."""
        doc = pymupdf.open(str(pdf_path))
        all_courses = []

        # Get headers from first page
        first_page = doc[0]
        first_page_words = first_page.get_text("words")
        if not first_page_words:
            return []

        # Find header line and get column boundaries
        header_words = self._find_header_lines(first_page_words)
        if not header_words:
            return []

        header_y_bottom = max(hw['y1'] for hw in header_words)
        column_boundaries = self._get_column_boundaries(header_words)

        # Process each page
        for page_num in range(len(doc)):
            self.logger.info(f"Processing page {page_num + 1} of {len(doc)}")
            page = doc[page_num]
            words = page.get_text("words")

            if not words:
                continue

            page_start_y = header_y_bottom if page_num == 0 else 0
            words_in_columns = self._assign_words_to_columns(words, column_boundaries, page_start_y)
            rows = self._cluster_words_into_rows(words_in_columns)

            page_courses = self._extract_course_info(rows, page_num)
            all_courses.extend(page_courses)

        doc.close()
        return self._validate_courses(all_courses)

    def _find_header_lines(self, words: List) -> List[Dict]:
        """Find header lines in PDF text."""
        # Implementation from pdf_to_text_v4.py
        lines = {}
        for w in words:
            x0, y0, x1, y1, text, block_no, line_no, word_no = w
            line_key = round(y0, 1)
            if line_key not in lines:
                lines[line_key] = []
            lines[line_key].append({
                'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'text': text
            })

        header_lines = []
        for y_line, wds in sorted(lines.items()):
            line_texts = [wd['text'].lower() for wd in wds]
            matches = sum(1 for h in EXPECTED_HEADERS if h.lower() in line_texts)
            if matches > len(EXPECTED_HEADERS) * 0.5:
                header_lines.append(wds)
            if len(header_lines) >= 5:
                break

        if not header_lines:
            return None

        header_words = [word for line in header_lines for word in line]
        return sorted(header_words, key=lambda x: x['x0'])

    def _get_column_boundaries(self, header_words: List[Dict]) -> List:
        """Determine column boundaries from header words."""
        # Implementation from pdf_to_text_v4.py
        found_columns = []
        used_indices = set()

        for expected in EXPECTED_HEADERS:
            candidates = [(i, hw) for i, hw in enumerate(header_words)
                          if expected.lower() in hw['text'].lower() and i not in used_indices]
            if candidates:
                i, hw = candidates[0]
                used_indices.add(i)
                found_columns.append((expected, hw['x0'], hw['x1']))
            else:
                found_columns.append((expected, None, None))

        found_columns = [fc for fc in found_columns if fc[1] is not None]
        found_columns.sort(key=lambda c: c[1])

        boundaries = []
        for i, (col_name, x_start, x_end) in enumerate(found_columns):
            tolerance = COLUMN_TOLERANCES.get(col_name, 5.0)

            if i == 0:
                left_bound = x_start - tolerance
            else:
                prev_col = boundaries[-1]
                left_bound = (prev_col[2] + x_start) / 2.0

            if i == len(found_columns) - 1:
                right_bound = x_end + 1000
            else:
                right_bound = x_end + tolerance

            boundaries.append((col_name, left_bound, right_bound))

        return boundaries

    def _assign_words_to_columns(self, words: List, column_boundaries: List, header_y_bottom: float) -> List[Dict]:
        """Assign words to appropriate columns."""
        data_words = [w for w in words if w[1] > header_y_bottom]
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

    def _cluster_words_into_rows(self, words_in_columns: List[Dict]) -> List[List[Dict]]:
        """Cluster words into rows based on vertical proximity."""
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
                gap = w['y0'] - last_y
                if gap > ROW_GAP_THRESHOLD:
                    rows.append(current_row)
                    current_row = [w]
                else:
                    current_row.append(w)
                last_y = w['y0']

        if current_row:
            rows.append(current_row)

        return rows

    def _extract_course_info(self, rows: List[List[Dict]], page_num: int) -> List[Dict]:
        """Extract course information from rows."""
        courses = []

        for row in rows:
            current_info = {}
            for word_info in row:
                text = word_info['text'].strip()
                column = word_info['col']

                if column == 'Seats' and current_info.get('seats') is None:
                    if text.isdigit() or text == "Full":
                        current_info['seats'] = 0 if text == "Full" else int(text)

                elif column == 'Capacity' and current_info.get('capacity') is None and text.isdigit():
                    current_info['capacity'] = int(text)

                elif column == 'CRN' and text.isdigit() and len(text) == 5:
                    current_info['crn'] = text

                if all(k in current_info for k in ['crn', 'seats', 'capacity']):
                    courses.append(current_info.copy())

        return courses

    def _validate_courses(self, courses: List[Dict]) -> List[Dict]:
        """Validate extracted course data."""
        validated_courses = []

        for course in courses:
            if all(key in course for key in ['crn', 'seats', 'capacity']):
                if course['capacity'] >= 0 and 0 <= course['seats'] <= course['capacity']:
                    validated_courses.append(course)

        self.logger.info(f"Validated {len(validated_courses)} out of {len(courses)} courses")
        return validated_courses

    def _fetch_timetable_data(self, subject_code: str, term_year: str) -> List:
        """Fetch course data from Timetable API."""
        timetable = Timetable()
        return timetable.subject_lookup(subject_code=subject_code, term_year=term_year, open_only=False)

    def _save_to_csv(self, merged_courses: List[Dict], pdf_name: str) -> Path:
        """Save merged course data to CSV file."""
        output_dir = Path("data/courses")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{pdf_name}_{timestamp}_courses.csv"

        import pandas as pd
        df = pd.DataFrame(merged_courses)
        df.to_csv(output_path, index=False)

        self.logger.info(f"Saved merged course data to {output_path}")
        return output_path
