import os
import sys
from typing import Optional

# ✅ Python Path 설정 (shared 모듈 접근용)  
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# ✅ 공통 설정 베이스 사용
from shared.config.base_settings import BaseServiceSettings

class Settings(BaseServiceSettings):
    """
    Material Assessment Service 설정
    공통 BaseServiceSettings을 상속하여 Material 특화 설정 추가
    """
    # ✅ 공통 설정에서 상속된 항목들:
    # - APP_NAME, VERSION, PORT, DEBUG, ENVIRONMENT
    # - REDIS_URL, REDIS_HOST, REDIS_PORT, REDIS_DB
    # - HOST, LOG_LEVEL, GATEWAY_URL
    
    # Material 서비스 특화 설정
    APP_NAME: str = "Material Assessment Service"
    PORT: int = 8004
    REDIS_URL: str = "redis://localhost:6379/1"  # Material Service는 DB 1 사용
    
    # 데이터베이스 설정 (향후 사용)
    DATABASE_URL: Optional[str] = None
    
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIRECTORY: str = "uploads"
    
    # 외부 서비스 연동 설정
    SASB_SERVICE_URL: str = "http://localhost:8003"

# 설정 인스턴스 생성
settings = Settings()

def get_settings() -> Settings:
    """설정 인스턴스 반환 (DI 컨테이너 호환성)"""
    return settings 