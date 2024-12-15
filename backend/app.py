from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# from .extraction.pdf_processor import PDFProcessor
from .extraction.pdf_processor_v1 import PDFProcessor
from .extraction.data_extractor import DataExtractor
from .utils.error_handler import handle_extraction_error
from .monitoring.monitoring import SystemStatus, MonitoringService
from pathlib import Path
import asyncio
import aiofiles
import pandas as pd
import logging
import json
from typing import List, Dict
from datetime import datetime
import shutil
import uuid
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Course Data Extractor")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
monitoring_service = MonitoringService() 
pdf_processor = PDFProcessor()
data_extractor = DataExtractor()

# Create necessary directories
Path("data/temp").mkdir(parents=True, exist_ok=True)
Path("data/individual").mkdir(parents=True, exist_ok=True)
Path("data/combined").mkdir(parents=True, exist_ok=True)


class ProcessingStatus:
    def __init__(self):
        self.tasks = {}

    def add_task(self, task_id: str, total_files: int):
        self.tasks[task_id] = {
            "total": total_files,
            "processed": 0,
            "failed": 0,
            "status": "processing",
            "errors": [],
            "results": []
        }

    def update_progress(self, task_id: str, success: bool, result: dict = None, error: str = None):
        if task_id not in self.tasks:
            return

        if success:
            self.tasks[task_id]["processed"] += 1
            if result:
                self.tasks[task_id]["results"].append(result)
        else:
            self.tasks[task_id]["failed"] += 1
            if error:
                self.tasks[task_id]["errors"].append(error)

        # Check if processing is complete
        task = self.tasks[task_id]
        if task["processed"] + task["failed"] == task["total"]:
            task["status"] = "completed"


status_tracker = ProcessingStatus()


async def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    """Save an uploaded file to the specified destination."""
    try:
        async with aiofiles.open(destination, 'wb') as out_file:
            content = await upload_file.read()
            await out_file.write(content)
        return destination
    except Exception as e:
        logger.error(f"Error saving file {upload_file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")


async def process_single_file(file_path: Path, task_id: str) -> Dict:
    """Process a single PDF file and extract course data."""
    start_time = time.time()
    try:
        # Extract text from PDF
        text = pdf_processor.process(file_path)

        # Validate extracted text
        if not pdf_processor.validate_output(text):
            raise ValueError("Extracted text does not contain valid course information")

        # Extract structured course data
        courses = data_extractor.extract_courses(text)

        # Save individual CSV
        output_csv = Path("data/individual") / f"{file_path.stem}_courses.csv"
        df = pd.DataFrame(courses)
        df.to_csv(output_csv, index=False)

        duration = time.time() - start_time
        result = {
            "filename": file_path.name,
            "courses_extracted": len(courses),
            "output_path": str(output_csv),
            "status": "success",
            "processing_time": duration
        }

        # Log success metrics
        monitoring_service.log_task_completion(task_id, True, duration)
        monitoring_service.log_extraction_metrics(task_id, file_path, len(courses))
        
        status_tracker.update_progress(task_id, True, result)
        return result

    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Error processing {file_path.name}: {str(e)}"
        logger.error(error_msg)
        
        # Log failure metrics
        monitoring_service.log_task_completion(task_id, False, duration)
        
        status_tracker.update_progress(task_id, False, error=error_msg)
        return {"filename": file_path.name, "status": "failed", "error": str(e)}


async def combine_csv_files(task_id: str):
    """Combine all individual CSV files into a single file."""
    try:
        all_files = list(Path("data/individual").glob("*_courses.csv"))
        if not all_files:
            return

        dfs = []
        for file in all_files:
            df = pd.read_csv(file)
            dfs.append(df)

        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path("data/combined") / f"all_courses_{timestamp}.csv"
            combined_df.to_csv(output_path, index=False)

            status_tracker.tasks[task_id]["combined_output"] = str(output_path)

    except Exception as e:
        logger.error(f"Error combining CSV files: {str(e)}")
        status_tracker.tasks[task_id]["errors"].append(f"Failed to combine CSV files: {str(e)}")


@app.post("/process")
async def process_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
) -> JSONResponse:
    """
    Process multiple PDF files and extract course information.

    Args:
        files: List of PDF files to process

    Returns:
        JSONResponse with task ID for tracking progress
    """
    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Initialize task tracking
    pdf_files = [f for f in files if f.filename.lower().endswith('.pdf')]
    status_tracker.add_task(task_id, len(pdf_files))

    try:
        # Create temporary directory for this task
        task_dir = Path("data/temp") / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Process each file
        for file in pdf_files:
            temp_path = task_dir / file.filename
            await save_upload_file(file, temp_path)

            # Process file in background
            background_tasks.add_task(process_single_file, temp_path, task_id)

        # Add task to combine CSVs after individual processing
        background_tasks.add_task(combine_csv_files, task_id)

        return JSONResponse(
            content={
                "task_id": task_id,
                "message": "Processing started",
                "total_files": len(pdf_files)
            },
            status_code=202
        )

    except Exception as e:
        error_details = handle_extraction_error(e)
        raise HTTPException(status_code=500, detail=error_details)

    finally:
        # Cleanup will be handled by background task
        background_tasks.add_task(lambda: shutil.rmtree(task_dir, ignore_errors=True))


@app.get("/status/{task_id}")
async def get_status(task_id: str) -> JSONResponse:
    """Get the current status of a processing task."""
    if task_id not in status_tracker.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return JSONResponse(content=status_tracker.tasks[task_id])


@app.get("/health")
async def health_check() -> JSONResponse:
    """Simple health check endpoint."""
    # return JSONResponse(content={"status": "healthy"})
    status, warnings = monitoring_service.check_health()
    return JSONResponse(content={
        "status": status,
        "warnings": warnings,
        "timestamp": datetime.utcnow().isoformat()
    })
