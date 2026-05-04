import boto3
from botocore.client import Config
import os
from core.logger import get_logger

logger = get_logger("storage")

ENDPOINT_URL = os.getenv("SUPABASE_STORAGE_ENDPOINT_URL")
ACCESS_KEY = os.getenv("SUPABASE_STORAGE_ACCESS_KEY")
SECRET_KEY = os.getenv("SUPABASE_STORAGE_SECRET_KEY")
REGION = os.getenv("SUPABASE_STORAGE_REGION", "us-east-2")
BUCKET_NAME = os.getenv("SUPABASE_STORAGE_BUCKET", "images")
PROJECT_ID = os.getenv("SUPABASE_PROJECT_ID")


def validate_storage_config():
    missing = [
        name for name, value in {
            "SUPABASE_STORAGE_ENDPOINT_URL": ENDPOINT_URL,
            "SUPABASE_STORAGE_ACCESS_KEY": ACCESS_KEY,
            "SUPABASE_STORAGE_SECRET_KEY": SECRET_KEY,
            "SUPABASE_PROJECT_ID": PROJECT_ID,
        }.items() if not value
    ]
    if missing:
        raise RuntimeError(f"Storage configuration missing: {', '.join(missing)}")

def get_s3_client():
    validate_storage_config()
    return boto3.client(
        's3',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION,
        config=Config(signature_version='s3v4')
    )

def upload_file_to_storage(file_obj, filename, content_type):
    """
    Uploads a file-like object to Supabase Storage via S3 protocol.
    Returns the public URL of the uploaded file.
    """
    s3 = get_s3_client()
    try:
        s3.upload_fileobj(
            file_obj,
            BUCKET_NAME,
            filename,
            ExtraArgs={'ContentType': content_type}
        )
        # Construct Public URL
        # Standard Supabase Storage Public URL pattern
        public_url = f"https://{PROJECT_ID}.supabase.co/storage/v1/object/public/{BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        logger.error(f"S3 Upload Error: {e}")
        raise e
