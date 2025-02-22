from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Any, Dict, Optional


class FrontendLogEntry(BaseModel):
    name: str
    level: int
    message: str
    details: Optional[Dict[str, Any]] = None
    environment: str


class Settings(BaseSettings):
    # Environment
    NODE_ENV: str = "development"

    # Base directory for the project
    BASE_DIR: Path = Path(__file__).parent.parent.parent

    # Storage directories (used in both environments)
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    DOWNLOAD_DIR: Path = BASE_DIR / "downloads"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Output file names
    ALL_GRADUATES_COURSES_FILENAME: str = "all_graduate_courses.csv"
    UNDERENROLLED_COURSES_FILENAME: str = "underenrolled_courses.csv"

    # Maximum file size (10 MB)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    # AWS Settings (only used in production)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-2"
    AWS_BUCKET_NAME: Optional[str] = None
    FILE_EXPIRATION_DAYS: int = 7

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ensure_directories()

    @property
    def is_production(self) -> bool:
        return self.NODE_ENV.lower() == "production"

    def ensure_directories(self):
        """Ensure all necessary directories exist"""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
