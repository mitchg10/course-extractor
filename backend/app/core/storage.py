# backend/app/core/storage.py

from typing import BinaryIO, Optional, List, Dict
from io import BytesIO
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from ..utils.logger import setup_logger
from pathlib import Path
import tempfile
from typing import Dict, Optional, List, BinaryIO, Union
from datetime import datetime, timedelta
from ..config import Settings

logger = setup_logger("storage")
settings = Settings()


class StorageBase:
    """Base storage class defining interface and common path handling"""

    def get_file_path(self, task_id: str, filename: str) -> str:
        """Standardize file path structure"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{task_id}/{timestamp}-{self.hyphenate(filename)}"

    def hyphenate(self, text: str) -> str:
        return text.lower().replace(" ", "-")


class LocalStorage(StorageBase):
    """Local storage implementation"""

    async def upload_file(self, file: UploadFile, task_id: str) -> str:
        """Save uploaded file and return relative path"""
        relative_path = self.get_file_path(task_id, file.filename)
        absolute_path = settings.UPLOAD_DIR / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        content = await file.read()
        with open(absolute_path, "wb") as f:
            f.write(content)
        await file.seek(0)

        logger.info(f"File uploaded to local storage: {absolute_path}")
        return relative_path

    def download_file(self, key: str) -> Optional[BinaryIO]:
        """Return file-like object for reading"""
        file_path = settings.UPLOAD_DIR / key
        if not file_path.exists():
            return None
    
        # Return BytesIO to match S3's behavior
        with open(file_path, 'rb') as f:
            data = BytesIO(f.read())

        logger.info(f"Local file downloaded: {key}")
        return data

    def save_csv(self, task_id: str, data_frame: pd.DataFrame, file_name: str) -> bool:
        """Save DataFrame as CSV, maintaining same path structure as S3"""
        try:
            relative_path = self.get_file_path(task_id, file_name)
            absolute_path = settings.DOWNLOAD_DIR / relative_path

            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            data_frame.to_csv(absolute_path, index=False)
            logger.info(f"CSV saved locally: {absolute_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save CSV locally: {str(e)}")
            return False

    def delete_file(self, key: str) -> bool:
        """Delete file using relative path and remove parent folder if empty"""
        try:
            file_path = settings.UPLOAD_DIR / key
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Local file deleted: {key}")
                # Check if parent directory is empty and remove it
                parent_dir = file_path.parent
                if not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    logger.info(f"Parent directory removed: {parent_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete local file: {str(e)}")
            return False


class S3Storage(StorageBase):
    """S3 storage implementation"""

    def __init__(self):
        super().__init__()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_BUCKET_NAME
        logger.info(f"Initialized S3 storage with bucket: {self.bucket_name}")

    async def upload_file(self, file: UploadFile, task_id: str) -> str:
        """Save uploaded file and return S3 key"""
        # key = self.get_upload_path(task_id, file.filename)
        key = self.get_file_path(task_id, file.filename)
        content = await file.read()

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            Expires=datetime.now() + timedelta(days=settings.FILE_EXPIRATION_DAYS)
        )
        await file.seek(0)

        logger.info(f"File uploaded to S3: {key}")
        return key

    def download_file(self, key: str) -> Optional[BinaryIO]:
        """Return file-like object for reading"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"S3 file downloaded: {key}")
            return response['Body']
        except ClientError:
            return None

    def save_csv(self, task_id, data_frame: pd.DataFrame, file_name: str) -> bool:
        """Save DataFrame as CSV using same path structure"""
        try:
            key = self.get_file_path(task_id, file_name)

            csv_buffer = BytesIO()
            data_frame.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
            logger.info(f"CSV saved to S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save CSV to S3: {str(e)}")
            return False

    def delete_file(self, key: str) -> bool:
        """Delete file using S3 key"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"File deleted from S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {str(e)}")
            return False
    
    def list_files(self, task_id: str) -> List[Dict[str, Union[str, int]]]:
        """List all files in a task directory with their sizes"""
        prefix = f"{task_id}/"
        response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        if 'Contents' not in response:
            return []
        return [{'key': obj['Key'], 'size': obj['Size']} for obj in response['Contents']]


def get_storage() -> StorageBase:
    """Factory function to get appropriate storage based on environment"""
    if settings.is_production:
        # In production, we need AWS credentials
        if not all([settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, settings.AWS_BUCKET_NAME]):
            raise ValueError("Production mode requires AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME)")
        logger.info("Using S3 storage in production")
        return S3Storage()

    # In development, always use local storage
    logger.info("Using local storage in development")
    return LocalStorage()
