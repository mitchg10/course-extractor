from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import shutil
import uuid
from pydantic import BaseModel

# from .pdf_processor import PDFProcessor
from .extraction.pdf_processor import PDFProcessor
from .monitoring import MonitoringService
from .utils.error_handler import handle_extraction_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Course Data Extractor")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
monitoring_service = MonitoringService()
pdf_processor = PDFProcessor()

# Create necessary directories
Path("data/temp").mkdir(parents=True, exist_ok=True)
Path("data/output").mkdir(parents=True, exist_ok=True)


class ProcessingStatus:
    """Track the status of PDF processing tasks."""

    def __init__(self):
        self.tasks: Dict[str, Dict] = {}

    def add_task(self, task_id: str, total_files: int, subject_code: str, term_year: str):
        self.tasks[task_id] = {
            "total_files": total_files,
            "processed_files": 0,
            "failed_files": 0,
            "status": "processing",
            "subject_code": subject_code,
            "term_year": term_year,
            "errors": [],
            "results": [],
            "start_time": datetime.now().isoformat()
        }

    def update_progress(self, task_id: str, success: bool, result: Optional[Dict] = None, error: Optional[str] = None):
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        if success:
            task["processed_files"] += 1
            if result:
                task["results"].append(result)
        else:
            task["failed_files"] += 1
            if error:
                task["errors"].append(error)

        # Update status if all files are processed
        if task["processed_files"] + task["failed_files"] >= task["total_files"]:
            task["status"] = "completed"
            task["end_time"] = datetime.now().isoformat()

            # Calculate success rate
            total = task["total_files"]
            successful = task["processed_files"]
            task["success_rate"] = (successful / total) * 100 if total > 0 else 0


class ProcessRequest(BaseModel):
    """Request model for PDF processing."""
    subject_code: str
    term_year: str


status_tracker = ProcessingStatus()


async def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    """Save an uploaded file to the specified destination."""
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return destination
    except Exception as e:
        logger.error(f"Error saving file {upload_file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")


async def process_single_file(file_path: Path, task_id: str, subject_code: str, term_year: str) -> Dict:
    """Process a single PDF file and extract course data."""
    try:
        # Start monitoring
        monitoring_service.log_task_start(task_id, str(file_path))
        start_time = datetime.now()

        # Process the PDF
        result = pdf_processor.process_pdf(file_path, subject_code, term_year)

        # Update monitoring
        duration = (datetime.now() - start_time).total_seconds()
        monitoring_service.log_task_completion(task_id, True, duration)

        # Update status
        status_tracker.update_progress(task_id, True, result)

        return result

    except Exception as e:
        error_msg = f"Error processing {file_path.name}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Update monitoring
        duration = (datetime.now() - start_time).total_seconds()
        monitoring_service.log_task_completion(task_id, False, duration)

        # Update status
        status_tracker.update_progress(task_id, False, error=error_msg)

        return {"filename": file_path.name, "status": "failed", "error": str(e)}

    finally:
        # Cleanup temporary file
        try:
            file_path.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")


@app.post("/process")
async def process_files(
    background_tasks: BackgroundTasks,
    request: ProcessRequest,
    files: List[UploadFile] = File(...)
) -> JSONResponse:
    """
    Process multiple PDF files and extract course information.

    Args:
        request: ProcessRequest containing subject_code and term_year
        files: List of PDF files to process
        background_tasks: FastAPI BackgroundTasks for async processing

    Returns:
        JSONResponse with task ID for tracking progress
    """
    print(f"Incoming request: {await request.json()}")
    print(f"Files: {[file.filename for file in files]}")

    # Validate input files
    pdf_files = [f for f in files if f.filename.lower().endswith('.pdf')]
    if not pdf_files:
        raise HTTPException(status_code=400, detail="No PDF files provided")

    # Generate task ID and initialize tracking
    task_id = str(uuid.uuid4())
    status_tracker.add_task(
        task_id,
        len(pdf_files),
        request.subject_code,
        request.term_year
    )
    logger.info(f"New task started: {task_id}")

    try:
        # Create temporary directory for this task
        task_dir = Path("data/temp") / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Save and process each file
        for pdf_file in pdf_files:
            temp_path = task_dir / f"{uuid.uuid4()}_{pdf_file.filename}"
            await save_upload_file(pdf_file, temp_path)
            logger.info(f"Saved file: {temp_path}")

            # Process file in background
            background_tasks.add_task(
                process_single_file,
                temp_path,
                task_id,
                request.subject_code,
                request.term_year
            )
            logger.info(f"Processing started for {temp_path}")
        
        return JSONResponse(
            content={
                "task_id": task_id,
                "message": "Processing started",
                "total_files": len(pdf_files)
            },
            status_code=202
        )

    except Exception as e:
        # Clean up task directory in case of error
        shutil.rmtree(task_dir, ignore_errors=True)

        error_details = handle_extraction_error(e)
        raise HTTPException(status_code=500, detail=error_details)


@app.get("/status/{task_id}")
async def get_status(task_id: str) -> JSONResponse:
    """Get the current status of a processing task."""
    if task_id not in status_tracker.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task_status = status_tracker.tasks[task_id]
    return JSONResponse(content=task_status)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Check the health status of the service."""
    status, warnings = monitoring_service.check_health()
    return JSONResponse(content={
        "status": status,
        "warnings": warnings,
        "timestamp": datetime.utcnow().isoformat()
    })

# Cleanup old tasks periodically (you might want to add this as a background task)


async def cleanup_old_tasks():
    """Clean up old temporary files and task statuses."""
    while True:
        try:
            # Clean up files older than 24 hours
            temp_dir = Path("data/temp")
            current_time = datetime.now()

            for task_dir in temp_dir.iterdir():
                if task_dir.is_dir():
                    dir_age = current_time - datetime.fromtimestamp(task_dir.stat().st_mtime)
                    if dir_age.days >= 1:
                        shutil.rmtree(task_dir, ignore_errors=True)

            # Clean up old task statuses
            old_tasks = [
                task_id for task_id, task in status_tracker.tasks.items()
                if task["status"] == "completed" and
                datetime.fromisoformat(task["end_time"]) < current_time.replace(day=current_time.day-1)
            ]

            for task_id in old_tasks:
                del status_tracker.tasks[task_id]

        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")

        await asyncio.sleep(3600)  # Run every hour


@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup."""
    asyncio.create_task(cleanup_old_tasks())
