# backend/app/main.py
from http.client import HTTPException
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import logging
from typing import List
import uuid
from pathlib import Path
import json

# from app.core.pdf_processor import process_pdf_files
from .core.pdf_processor import PdfProcessor
from .utils.logger import setup_logger
from .api.models import FileInfo, FileListResponse, ProcessingResponse, ProcessingStatus
from .config import Settings
from .routes import router

# Initialize settings and logger
settings = Settings()
logger = setup_logger("course_extractor")

app = FastAPI(title="Course Extractor API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    expose_headers=["Content-Disposition", "Content-Type"],
    max_age=600,
)

# Include the router
app.include_router(router)

# Store background tasks status
processing_tasks = {}


@app.post("/process", response_model=ProcessingResponse)
async def process_files(
    files: List[UploadFile] = File(...),
    metadata: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    """
    Process uploaded PDF files asynchronously
    """
    try:
        # Parse the metadata
        metadata_list = json.loads(metadata)

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Create temporary directory for uploaded files
        temp_dir = Path(settings.UPLOAD_DIR) / task_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded files and prepare metadata
        saved_files = []
        file_metadata = []

        for file, meta in zip(files, metadata_list):
            # Save file
            file_path = temp_dir / file.filename
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            saved_files.append(str(file_path))

            # Prepare metadata
            file_metadata.append({
                'file_path': str(file_path),
                'subject_code': meta['subject_code'],
                'term_year': meta['term_year']
            })

            # Log the saved file
            logger.info(f"Saved file: {file_path} with metadata: {meta}")

        logger.info(f"Saved {len(saved_files)} files for processing. Task ID: {task_id}")

        # Create a Pdf Processor
        processor = PdfProcessor()

        # Add background task for processing
        background_tasks.add_task(
            processor.process_pdf_files,
            task_id,
            file_metadata,
            processing_tasks
        )

        return ProcessingResponse(task_id=task_id, status="processing")

    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        raise


@app.get("/status/{task_id}", response_model=ProcessingStatus)
async def get_status(task_id: str):
    """
    Get the status of a processing task
    """
    if task_id not in processing_tasks:
        return ProcessingStatus(status="not_found")

    return ProcessingStatus(
        status=processing_tasks[task_id]["status"],
        progress=processing_tasks[task_id].get("progress", 0),
        result=processing_tasks[task_id].get("result"),
        error=processing_tasks[task_id].get("error")
    )


@app.get("/available-files/{task_id}")
async def get_available_files(task_id: str):
    """Get a list of available files for download for a specific task."""
    try:
        # Check if task exists and is completed
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        if processing_tasks[task_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail="Task not completed yet")

        files = []
        download_dir = settings.DOWNLOAD_DIR

        # Look for specific files generated for this task
        patterns = [
            f"{task_id}_all_graduate_courses.csv",
            f"{task_id}_underenrolled_courses.csv"
        ]

        for pattern in patterns:
            file_path = download_dir / pattern
            if file_path.exists():
                files.append(
                    FileInfo(
                        filename=file_path.name,
                        size=file_path.stat().st_size,
                        type="text/csv"
                    )
                )
        return FileListResponse(files=files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    """Download a specific file for a task."""
    try:
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        if processing_tasks[task_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail="Task not completed yet")

        file_path = settings.DOWNLOAD_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
