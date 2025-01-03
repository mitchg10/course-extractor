# backend/app/api/models.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ProcessingResponse(BaseModel):
    task_id: str
    status: str

class ProcessingStatus(BaseModel):
    status: str
    progress: Optional[float] = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None