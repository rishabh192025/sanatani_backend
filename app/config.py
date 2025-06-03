# app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional # Added Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str ="postgresql://postgres:sanatani_db@sanatanidb.criqcqc42dui.eu-north-1.rds.amazonaws.com:5432/sanatani_db"
    # Async Database URL
    DATABASE_URL_ASYNC: str ="postgresql+asyncpg://postgres:sanatani_db@sanatanidb.criqcqc42dui.eu-north-1.rds.amazonaws.com:5432/sanatani_db"

    # Security
    SECRET_KEY: str = "your-secret-key-here-please-change-me" # Make sure to change this
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"] # Added localhost:8000 for backend dev
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".mp3", ".jpg", ".png", ".jpeg", ".mp4", ".mov"] # Added video
    
    # External Services (Placeholders - fill in .env)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"
    AWS_S3_BUCKET_NAME: Optional[str] = None # Renamed for clarity
    
    # Email (Placeholders - fill in .env)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = "noreply@yourdomain.com"
    
    # Project
    PROJECT_NAME: str = "Sanatani API"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()