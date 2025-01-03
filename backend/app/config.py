# backend/app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Base directory for the project
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    
    # Directory for temporary file uploads
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    
    # Directory for backend logs
    BACKEND_LOG_DIR: Path = BASE_DIR / "logs" / "backend"

    # Frontend log directory
    FRONTEND_LOG_DIR: Path = BASE_DIR / "logs" / "frontend"
    
    # Maximum file size (10 MB)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    
    class Config:
        env_file = ".env"