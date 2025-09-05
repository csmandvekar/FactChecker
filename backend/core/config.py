import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # File Storage
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "supabase")  # supabase, local, s3, minio
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")  # service role key preferred for server-side
    SUPABASE_STORAGE_BUCKET: Optional[str] = os.getenv("SUPABASE_STORAGE_BUCKET", "uploads")
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")
    S3_ACCESS_KEY: Optional[str] = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = os.getenv("S3_SECRET_KEY")
    S3_REGION: Optional[str] = os.getenv("S3_REGION", "us-east-1")
    
    # MinIO Configuration
    MINIO_ENDPOINT: Optional[str] = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: Optional[str] = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: Optional[str] = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: Optional[str] = os.getenv("MINIO_BUCKET_NAME", "deepverify")
    
    # Local Storage
    LOCAL_STORAGE_PATH: str = os.getenv("LOCAL_STORAGE_PATH", "./uploads")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]
    
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "DeepVerify Studio"
    
    # Model Paths
    CASIA_MODEL_PATH: str = os.getenv("CASIA_MODEL_PATH", "./models/casia_cnn.pth")
    
    class Config:
        env_file = ".env"

settings = Settings()
