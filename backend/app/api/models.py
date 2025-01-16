# backend/app/api/models.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ProcessingResponse(BaseModel):
    task_id: str
    status: str


class ProcessingStatus(BaseModel):
    status: str
    progress: Optional[float] = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FileInfo(BaseModel):
    filename: str
    size: int
    type: str = "text/csv"


class FileListResponse(BaseModel):
    files: List[FileInfo]

