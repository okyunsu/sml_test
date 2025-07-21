import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings.
    Values are loaded from environment variables defined in the .env file.
    """
    # Service Information
    APP_NAME: str = "SASB Analysis Service"
    APP_VERSION: str = "1.0.0"
    PORT: int = 8003

    # Naver API Credentials for News Crawling
    NAVER_CLIENT_ID: str = os.getenv("NAVER_CLIENT_ID", "your_naver_client_id")
    NAVER_CLIENT_SECRET: str = os.getenv("NAVER_CLIENT_SECRET", "your_naver_client_secret")
    
    # ML Model Configuration
    MODEL_BASE_PATH: Optional[str] = os.getenv("MODEL_BASE_PATH", "/app/models") # Path inside the container where models are mounted
    MODEL_NAME: Optional[str] = os.getenv("MODEL_NAME", "test222") # Name of the specific model directory

    # Celery and Redis Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # ML Model Loading Control
    DISABLE_ML_MODEL: bool = os.getenv("DISABLE_ML_MODEL", "false").lower() == "true"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 