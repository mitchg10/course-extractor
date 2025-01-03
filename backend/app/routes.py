# Add to your existing routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from .utils.logger import setup_logger
import logging

router = APIRouter()

# Create a dedicated frontend logger using your existing setup
frontend_logger = setup_logger("frontend", log_dir="frontend")

class FrontendLogEntry(BaseModel):
    name: str
    level: int
    message: str
    details: Optional[Dict[str, Any]] = None
    environment: str

@router.post("/frontend-logs")
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