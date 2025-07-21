from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Material Assessment Service 설정"""
    
    # 기본 설정
    APP_NAME: str = "Material Assessment Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8004
    
    # 데이터베이스 설정 (향후 사용)
    DATABASE_URL: Optional[str] = None
    
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIRECTORY: str = "uploads"
    
    # 외부 서비스 연동 설정
    GATEWAY_URL: str = "http://localhost:8080"
    SASB_SERVICE_URL: str = "http://localhost:8003"
    
    # Redis 설정 (캐싱용)
    REDIS_URL: str = "redis://localhost:6379/1"
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 설정 인스턴스 생성
settings = Settings() 