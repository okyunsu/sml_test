import os
import sys
from typing import Optional

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# ✅ 공통 설정 베이스 사용
from shared.config.base_settings import MLServiceSettings

class Settings(MLServiceSettings):
    """
    SASB Analysis Service 설정
    공통 MLServiceSettings을 상속하여 SASB 특화 설정 추가
    """
    # ✅ 공통 설정에서 상속된 항목들:
    # - APP_NAME, VERSION, PORT, DEBUG, ENVIRONMENT
    # - REDIS_URL, REDIS_HOST, REDIS_PORT, REDIS_DB
    # - MODEL_BASE_PATH, MODEL_NAME, DISABLE_ML_MODEL
    # - CELERY_BROKER_URL, CELERY_RESULT_BACKEND
    # - NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
    
    # SASB 서비스 특화 설정
    APP_NAME: str = "SASB Analysis Service"
    PORT: int = 8003
    
    # 기존 호환성 유지용 (deprecated)
    APP_VERSION: str = "1.0.0"  # VERSION과 동일

settings = Settings()

def get_settings() -> Settings:
    """설정 인스턴스 반환 (DI 컨테이너 호환성)"""
    return settings 