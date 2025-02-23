import datetime
import os
import tempfile
from fastapi import APIRouter, FastAPI, UploadFile, File, BackgroundTasks, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import logging
from typing import Any, Dict, List, Optional
import uuid
from pathlib import Path
import json

from .core.pdf_processor import PdfProcessor
from .utils.logger import setup_logger
from .api.models import FileInfo, FileListResponse, ProcessingResponse, ProcessingStatus
from .core.storage import get_storage
from .config import Settings, FrontendLogEntry

# Initialize necessary components
settings = Settings()
api_logger = setup_logger("course_extractor")
frontend_logger = setup_logger("frontend", log_dir="frontend")
storage = get_storage()

app = FastAPI(title="Course Extractor API")

origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8000",  # FastAPI server
    "https://course-extractor-rior.onrender.com",  # Render deployment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
)

api_router = APIRouter(prefix="/api")

# Store background tasks status
processing_tasks = {}


@api_router.post("/frontend-logs")
async def save_frontend_log(log_entry: FrontendLogEntry):
    try:
        # Format the log message
        message = f"{log_entry.message}"
        if log_entry.details:
            message += f" | Details: {log_entry.details}"

        # Log using your existing logger
        frontend_logger.log(log_entry.level, message)

        return {"status": "success", "message": "Log entry saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/process", response_model=ProcessingResponse)
async def process_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    metadata: str = Form(...),
):
    """
    Process uploaded PDF files asynchronously
    """
    try:
        # Parse the metadata
        metadata_list = json.loads(metadata)

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Store files and get their storage paths/keys
        file_metadata = []
        for file, meta in zip(files, metadata_list):
            try:
                # Upload file using appropriate storage
                storage_path = await storage.upload_file(file, task_id=f"{task_id}")

                # Prepare metadata with storage path
                file_metadata.append({
                    'file_path': storage_path,
                    'subject_code': meta['subject_code'],
                    'term_year': meta['term_year']
                })

                api_logger.info(f"Stored file: {storage_path}")

            except Exception as e:
                api_logger.error(f"Failed to store file {file.filename}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")

        # Initialize processing tasks status
        processing_tasks[task_id] = {"status": "processing", "progress": 0}

        # Create a PDF Processor
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
        api_logger.error(f"Error processing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/status/{task_id}", response_model=ProcessingStatus)
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


@api_router.get("/available-files/{task_id}")
async def get_available_files(task_id: str):
    """Get a list of available files for download for a specific task."""
    try:
        # Check if task exists and is completed
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        if processing_tasks[task_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail="Task not completed yet")

        files = []
        patterns = [
            settings.ALL_GRADUATES_COURSES_FILENAME,
            settings.UNDERENROLLED_COURSES_FILENAME
        ]

        if settings.is_production:
            # List files from S3
            s3_files = storage.list_files(task_id)
            for s3_file in s3_files:
                if any(pattern in s3_file['key'] for pattern in patterns):
                    files.append(
                        FileInfo(
                            filename=Path(s3_file['key']).name,
                            size=s3_file['size'],
                            type="text/csv"
                        )
                    )
        else:
            # List files from local storage
            download_dir = settings.DOWNLOAD_DIR
            for pattern in patterns:
                for file_path in download_dir.glob(f"{task_id}/*-{pattern}"):
                    if file_path.exists():
                        api_logger.info(f"Found file: {file_path}")
                        files.append(
                            FileInfo(
                                filename=file_path.name,
                                size=file_path.stat().st_size,
                                type="text/csv"
                            )
                        )

        return FileListResponse(files=files)
    except Exception as e:
        api_logger.error(f"Error listing available files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str, background_tasks: BackgroundTasks):
    """Download a specific file for a task."""
    try:
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        if processing_tasks[task_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail="Task not completed yet")

        if settings.is_production:
            # Get file from S3
            s3_key = f"{task_id}/{filename}"
            file_content = storage.download_file(s3_key)

            if not file_content:
                raise HTTPException(status_code=404, detail="File not found")

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content.read())
                temp_path = temp_file.name

            # Add the cleanup task properly
            async def cleanup_temp_file():
                os.unlink(temp_path)

            background_tasks.add_task(cleanup_temp_file)

            return FileResponse(
                path=temp_path,
                filename=filename,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # Get file from local storage
            file_path = settings.DOWNLOAD_DIR / task_id / filename
            api_logger.info(f"Downloading file: {file_path}")
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found: {file_path}")

            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    except Exception as e:
        api_logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/health")
async def health_check():
    """Health check endpoint for the application"""
    try:
        status = {
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "environment": settings.NODE_ENV,
        }

        # Test storage
        if settings.is_production:
            try:
                # Test S3 connection
                storage.s3_client.head_bucket(Bucket=settings.AWS_BUCKET_NAME)
                status["storage"] = "s3_connected"
            except Exception as e:
                status.update({
                    "status": "unhealthy",
                    "storage_error": str(e)
                })
        else:
            # Test local storage directories
            status["storage"] = "local_storage"
            for dir_name, dir_path in {
                "upload": settings.UPLOAD_DIR,
                "download": settings.DOWNLOAD_DIR,
                "logs": settings.BACKEND_LOG_DIR
            }.items():
                if not dir_path.exists():
                    status.update({
                        "status": "unhealthy",
                        "storage_error": f"{dir_name} directory not found"
                    })

        return status
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e)
        }

# Include the API router
app.include_router(api_router)

# Set up static files
static_directory = Path("/app/frontend/dist")
if settings.is_production and static_directory.exists():
    try:
        app.mount("/assets", StaticFiles(directory=str(static_directory / "assets")), name="assets")
        app.mount("/", StaticFiles(directory=str(static_directory), html=True), name="static")
        api_logger.info(f"Mounted static files from {static_directory}")
    except Exception as e:
        api_logger.error(f"Failed to mount static files: {str(e)}")
else:
    pass

# Catch-all


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Skip API routes
    if full_path.startswith(("api/", "process", "status", "available-files", "download", "health")):
        raise HTTPException(404, "API route not found")

    # In development mode, don't try to serve frontend
    if not settings.is_production:
        raise HTTPException(404, "In development mode, use Vite dev server")

    # Serve index.html for all other routes
    index_path = static_directory / "index.html"
    if index_path.exists():
        api_logger.info(f"Serving frontend from {index_path}")
        return FileResponse(str(index_path))
    else:
        api_logger.error(f"Frontend not found at {index_path}")
        raise HTTPException(404, "Frontend not found")


if __name__ == "__main__":
    port = os.getenv("API_PORT", 8000)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=not settings.is_production)
    for route in app.routes:
        api_logger(f"Route: {route.path} - {route.methods}")
