import boto3
import os
from botocore.exceptions import ClientError
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_s3_connection():
    """Test S3 credentials and bucket access"""
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        bucket_name = os.getenv('AWS_BUCKET_NAME')

        # Test 1: List buckets (tests credentials)
        logger.info("Testing AWS credentials...")
        s3_client.list_buckets()
        logger.info("✅ Credentials are valid")

        # Test 2: Check bucket exists and is accessible
        logger.info(f"Testing access to bucket: {bucket_name}")
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info("✅ Bucket is accessible")

        # Test 3: Upload a test file
        test_key = f"test/test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        logger.info(f"Testing file upload to {test_key}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body="This is a test file"
        )
        logger.info("✅ File upload successful")

        # Test 4: Download the test file
        logger.info("Testing file download")
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=test_key
        )
        content = response['Body'].read().decode('utf-8')
        assert content == "This is a test file"
        logger.info("✅ File download successful")

        # Test 5: List files in test directory
        logger.info("Testing file listing")
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix="test/"
        )
        assert 'Contents' in response
        logger.info("✅ File listing successful")

        # Test 6: Delete test file
        logger.info("Testing file deletion")
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=test_key
        )
        logger.info("✅ File deletion successful")

        logger.info("🎉 All S3 operations tested successfully!")
        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"❌ AWS Error: {error_code} - {error_message}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    # Check if environment variables are set
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.info("Please set the following environment variables:")
        logger.info("export AWS_ACCESS_KEY_ID='your_access_key'")
        logger.info("export AWS_SECRET_ACCESS_KEY='your_secret_key'")
        logger.info("export AWS_BUCKET_NAME='your_bucket_name'")
        logger.info("export AWS_REGION='your_region' # Optional, defaults to us-east-1")
    else:
        test_s3_connection()
