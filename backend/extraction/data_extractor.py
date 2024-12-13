from typing import Dict, List, Optional
import logging
from pathlib import Path
from datetime import datetime
import json
import os


class DataExtractor:
    """
    Temporary implementation of DataExtractor that saves raw text output
    and returns dummy structured data for testing the pipeline.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Create output directory for raw text files
        self.output_dir = Path("data/raw_text")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_courses(self, text: str) -> List[Dict]:
        """
        Save raw text to file and return dummy structured data.

        Args:
            text (str): Input text from PDF processor

        Returns:
            List[Dict]: List of dummy course information for testing
        """
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"raw_text_{timestamp}.txt"

            # Save raw text with metadata
            metadata = {
                "timestamp": timestamp,
                "characters": len(text),
                "lines": len(text.splitlines())
            }

            with open(output_file, "w", encoding="utf-8") as f:
                # Write metadata as JSON comment
                f.write(f"/* Metadata:\n{json.dumps(metadata, indent=2)}\n*/\n\n")
                # Write actual text content
                f.write(text)

            self.logger.info(
                f"Saved raw text to {output_file}",
                extra={
                    "metadata": metadata,
                    "output_path": str(output_file)
                }
            )

            # Return dummy course data for testing
            return [
                {
                    "course_code": "CS1101",
                    "title": "Dummy Course 1",
                    "instructor": "TBA",
                    "schedule": "MWF 10:00-10:50",
                    "location": "TBA",
                    "raw_text_file": str(output_file)
                },
                {
                    "course_code": "CS1102",
                    "title": "Dummy Course 2",
                    "instructor": "TBA",
                    "schedule": "TR 11:00-12:15",
                    "location": "TBA",
                    "raw_text_file": str(output_file)
                }
            ]

        except Exception as e:
            self.logger.error(
                f"Failed to process text: {str(e)}",
                exc_info=True,
                extra={"text_length": len(text)}
            )
            # Return empty list on error
            return []

    def get_raw_text_files(self) -> List[Path]:
        """
        Get list of all saved raw text files.

        Returns:
            List[Path]: List of paths to raw text files
        """
        return sorted(self.output_dir.glob("raw_text_*.txt"))
