from typing import List, Dict
from pathlib import Path
import pymupdf
import re
import pandas as pd
from ..utils.logger import setup_logger
from .merger import CourseDataMerger
from .constants import ENGINEERING_CODES, EXPECTED_HEADERS, IGNORE_COURSES
from ..config import Settings
from pyvt import Timetable

settings = Settings()

# TODO: Edit file paths and verify they download to the user's machine

class PdfProcessor:
    def __init__(self):
        self.row_gap_threshold = 10.0
        self.column_tolerances = {
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
        self.all_graduate_courses = []
        self.underenrolled_courses = []
        self.logger = setup_logger("pdf_processor")

    def process_pdf_files(self,
                          task_id: str,
                          file_metadata: List[dict],
                          processing_tasks: dict) -> None:
        """
        Process PDF files and update task status
        """
        try:
            processing_tasks[task_id] = {"status": "processing", "progress": 0}
            self.logger.info(f"Starting processing task {task_id}")

            results = []
            total_files = len(file_metadata)

            self.logger.info(f"Processing {total_files} files")

            for index, metadata in enumerate(file_metadata, 1):
                # Update progress
                progress = (index / total_files) * 100
                processing_tasks[task_id]["progress"] = progress

                try:
                    self.logger.info(f"Processing file {index}/{total_files}: {metadata}")

                    # Process single PDF file
                    file_path = metadata['file_path']
                    subject_code = metadata['subject_code']
                    term_year = metadata['term_year']

                    # Process PDF content
                    pdf_courses = self._process_pdf(file_path)

                    # Fetch timetable data using metadata
                    timetable_data = self._fetch_from_timetable(subject_code, term_year)

                    # Merge data
                    merger = CourseDataMerger()
                    merger.load_pdf_data(pdf_courses)
                    merger.load_timetable_data(timetable_data)
                    merged_courses = merger.merge_course_data()

                    # Get stats
                    stats = merger.get_statistics()
                    results.append({
                        "file": Path(file_path).name,
                        "courses": len(merged_courses),
                        "stats": stats
                    })
                    self.logger.info(f"Department {subject_code} statistics:")
                    for key, value in stats.items():
                        self.logger.info(f"  {key}: {value}")

                    # Filter graduate courses
                    graduate_courses = self._filter_graduate_courses(merged_courses)
                    self.all_graduate_courses.extend(graduate_courses)

                    self.logger.info(f"Processed file {index}/{total_files}: {Path(file_path).name}")

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path}: {str(e)}")
                    results.append({
                        "file": Path(file_path).name,
                        "error": str(e)
                    })

            # If graduate courses are found
            if self.all_graduate_courses:
                # Save them
                output_file = f"{task_id}_all_graduate_courses.csv"
                self._save_to_csv(self.all_graduate_courses, output_file)

                # Find underenrolled courses
                underenrolled = self._find_underenrolled_classes()
                if underenrolled:
                    under_file_name = f"{task_id}_underenrolled_courses.csv"
                    self._save_to_csv(underenrolled, under_file_name)

            # Update task status with results
            processing_tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "result": {"files": results}
            })

            # Cleanup temporary files
            self._cleanup_files([m['file_path'] for m in file_metadata])

        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            processing_tasks[task_id].update({
                "status": "failed",
                "error": str(e)
            })

    def _fetch_from_timetable(self, subject_code: str, term_year: str = None):
        # Create a timetable object
        timetable = Timetable()
        # Return all possible subjects
        return timetable.subject_lookup(subject_code=subject_code, term_year=term_year, open_only=False)

    def _cleanup_files(self, file_paths: List[str]) -> None:
        """
        Clean up temporary files after processing
        """
        for file_path in file_paths:
            try:
                Path(file_path).unlink()
                self.logger.debug(f"Cleaned up file: {file_path}")
            except Exception as e:
                self.logger.error(f"Error cleaning up file {file_path}: {str(e)}")

        # Try to remove parent directory if empty
        try:
            parent_dir = Path(file_paths[0]).parent
            if parent_dir.exists() and not any(parent_dir.iterdir()):
                parent_dir.rmdir()
                self.logger.debug(f"Removed empty directory: {parent_dir}")
        except Exception as e:
            self.logger.error(f"Error removing directory: {str(e)}")

    def _process_pdf(self, file_path: Path):
        """
        Process all pages in the PDF and extract course information.
        Headers are only on the first page, so we'll use those column boundaries for all pages.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            list: List of validated course dictionaries
        """
        # Open PDF file
        doc = pymupdf.open(file_path)
        all_courses = []

        # Get headers from first page only
        first_page = doc[0]
        first_page_words = first_page.get_text("words")

        if not first_page_words:
            return []

        # Find header line and get column boundaries
        header_words = self._find_header_lines(first_page_words, EXPECTED_HEADERS)
        if not header_words:
            return []

        header_y_bottom = max(hw['y1'] for hw in header_words)
        column_boundaries = self._get_column_boundaries(header_words)

        # Process each page using the column boundaries from first page
        for page_num in range(len(doc)):
            self.logger.info(f"Processing page {page_num + 1} of {len(doc)}")
            page = doc[page_num]
            words = page.get_text("words")

            # Skip empty pages
            if not words:
                continue

            # For first page, use the header_y_bottom we found
            # For other pages, we can start from top of page (or use a small offset)
            page_start_y = header_y_bottom if page_num == 0 else 0

            words_in_columns = self._assign_words_to_columns(words, column_boundaries, page_start_y)
            rows = self._cluster_words_into_rows(words_in_columns)

            # Extract course info from this page
            page_courses = self._extract_course_info(rows, page_num)
            self.logger.info(f"Found {len(page_courses)} courses on page {page_num + 1}")
            all_courses.extend(page_courses)

        doc.close()

        return all_courses

    def _find_header_lines(self, words, expected_headers):
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

    def _get_column_boundaries(self, header_words):
        """
        Determine column boundaries based on the header words.
        Returns a list of (column_name, min_x, max_x) tuples.
        """
        # Match header_words to expected headers in sorted order
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
                found_columns.append((expected, None, None))

        # Now that we have a list of (header, x0, x1), fill in missing columns by approximating boundaries.
        found_columns = [fc for fc in found_columns if fc[1] is not None]
        found_columns.sort(key=lambda c: c[1])

        # Determine boundaries between columns
        boundaries = []
        for i, (col_name, x_start, x_end) in enumerate(found_columns):
            tolerance = self.column_tolerances.get(col_name, 5.0)
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
                # Temporarily, set right_bound to x_end
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

    def _assign_words_to_columns(self, words, column_boundaries, header_y_bottom):
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

    def _cluster_words_into_rows(self, words_in_columns):
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
                if gap > self.row_gap_threshold:
                    # New row
                    rows.append(current_row)
                    current_row = [w]
                else:
                    current_row.append(w)
                last_y = w['y0']
        if current_row:
            rows.append(current_row)

        return rows

    def _extract_course_info(self, rows, page_num):
        """
        Extract and validate CRN, Seats, and Capacity information from rows data.

        Args:
            rows (list): List of row data from PDF extraction
            page_num (int): Page number for logging

        Returns:
            list: List of dictionaries containing validated CRN, Seats, and Capacity
        """
        courses = []
        current_info = {}

        self.logger.info(f"=== Processing Pages ===")
        self.logger.info(f"Number of rows to process: {len(rows)} from page {page_num + 1}")

        for row in rows:
            current_info = {}
            for word_info in row:
                text = word_info['text'].strip()
                column = word_info['col']

                if column == 'Seats' and current_info.get('seats') is None:
                    if text.isdigit() or "Full" in text:
                        current_info['seats'] = 0 if text == "Full" else int(text)

                elif column == 'Capacity' and current_info.get('capacity') is None and text.isdigit():
                    current_info['capacity'] = int(text)

                elif column == 'CRN' and text.isdigit() and len(text) == 5:
                    current_info['crn'] = text

                # If we have all required fields, add the course
                if 'crn' in current_info and 'seats' in current_info and 'capacity' in current_info:
                    courses.append(current_info.copy())
                    current_info = {}

        return courses

    def _filter_graduate_courses(self, merged_courses):
        graduate_courses = []
        for course in merged_courses:
            # Extract the numeric part of the course code
            match = re.search(r'\d+', course['code'])
            if match and int(match.group()) >= 5000:
                # course['seats'] = course['capacity'] - course['seats']
                graduate_courses.append(course.copy())
        return graduate_courses

    def _save_to_csv(self, data, filename):
        output_path = settings.DOWNLOAD_DIR / filename
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        self.logger.info(f"Saved data to {output_path}")

    def _find_underenrolled_classes(self):
        # Group courses by code and name to handle cross-listings
        course_groups = {}
        for course in self.all_graduate_courses:
            if course['name'] in IGNORE_COURSES:
                continue

            key = (course['code'], course['name'])
            if key not in course_groups:
                course_groups[key] = {
                    'courses': [],
                    'total_seats': 0,
                    'total_capacity': 0
                }

            group = course_groups[key]
            group['courses'].append(course)
            group['total_seats'] += course['seats']
            group['total_capacity'] += course['capacity']

        # Find underenrolled courses/groups
        underenrolled = []
        for (code, name), group in course_groups.items():
            if group['total_seats'] < 6:
                # Use the first course as base and update with combined totals
                base_course = group['courses'][0].copy()
                base_course['seats'] = group['total_seats']
                base_course['capacity'] = group['total_capacity']
                base_course['cross_listed'] = len(group['courses']) > 1

                underenrolled.append(base_course)
                self.logger.info(f"Underenrolled {'combined ' if base_course['cross_listed'] else ''}"
                                 f"course: {code}, {base_course['crn']} - Seats: {base_course['seats']}")

        self.logger.info(f"Found {len(underenrolled)} underenrolled courses")
        return underenrolled
