from minio import Minio
from minio.error import S3Error
import os
from dotenv import load_dotenv

load_dotenv()

# Use os.getenv to read from the .env file
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin123")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "edu-platform")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)

def ensure_bucket():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            print(f"✅ Created bucket: {BUCKET_NAME}")
    except S3Error as e:
        print("❌ MinIO error:", e)
        raise