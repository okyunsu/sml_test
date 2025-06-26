import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 네이버 API 설정
    naver_client_id: str = os.getenv("NAVER_CLIENT_ID", "")
    naver_client_secret: str = os.getenv("NAVER_CLIENT_SECRET", "")
    
    # 서비스 설정
    service_port: int = int(os.getenv("SERVICE_PORT", "8002"))
    service_host: str = os.getenv("SERVICE_HOST", "0.0.0.0")
    
    # API 설정
    naver_search_url: str = "https://openapi.naver.com/v1/search/news.json"
    max_display_count: int = 100  # 네이버 API 최대 결과 수
    default_display_count: int = 10
    
    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ML 서비스 연동 설정 (newstun-service와 통신)
    ml_service_url: str = os.getenv("ML_SERVICE_URL", "http://localhost:8004")
    
    # 모델 설정
    model_name: str = os.getenv("MODEL_NAME", "test123")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 전역 설정 인스턴스
settings = Settings() 