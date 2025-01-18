# backend/app/core/storage.py

import os
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from ..utils.logger import setup_logger
import logging
from typing import Optional, List, BinaryIO
from datetime import datetime, timedelta

logger = setup_logger("s3_storage")

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        self.expiration_days = int(os.getenv('FILE_EXPIRATION_DAYS', '7'))

    async def upload_file(self, file: UploadFile, folder: str = "uploads") -> str:
        """Upload a file to S3 and return its key."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"{folder}/{timestamp}_{file.filename}"

            # Read file content
            content = await file.read()

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                Expires=datetime.now() + timedelta(days=self.expiration_days)
            )

            await file.seek(0)  # Reset file pointer
            return key
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            raise

    def download_file(self, key: str) -> Optional[BinaryIO]:
        """Download a file from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    def get_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for file download."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise

    def list_files(self, prefix: str = "") -> List[dict]:
        """List all files in a specific prefix/folder."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
            return files
        except ClientError as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise

    def delete_file(self, key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False

    def cleanup_expired_files(self):
        """Delete files older than expiration_days."""
        try:
            expiration_date = datetime.now() - timedelta(days=self.expiration_days)
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)

            for obj in response.get('Contents', []):
                if obj['LastModified'] < expiration_date:
                    self.delete_file(obj['Key'])

        except ClientError as e:
            logger.error(f"Failed to cleanup expired files: {str(e)}")
            raise
