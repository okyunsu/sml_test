from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
from pathlib import Path

class BaseServiceSettings(BaseSettings):
    """모든 서비스의 기본 설정 클래스"""
    
    # === 기본 서비스 정보 ===
    APP_NAME: str = Field(..., description="서비스 이름")
    VERSION: str = Field(default="1.0.0", description="서비스 버전")
    DEBUG: bool = Field(default=False, description="디버그 모드")
    ENVIRONMENT: str = Field(default="development", description="실행 환경 (development/staging/production)")
    
    # === 서버 설정 ===
    HOST: str = Field(default="0.0.0.0", description="서버 호스트")
    PORT: int = Field(..., description="서버 포트")
    
    # === 로깅 설정 ===
    LOG_LEVEL: str = Field(default="INFO", description="로그 레벨")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="로그 포맷"
    )
    
    # === Redis 설정 ===
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis 연결 URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis 호스트")
    REDIS_PORT: int = Field(default=6379, description="Redis 포트")
    REDIS_DB: int = Field(default=0, description="Redis 데이터베이스 번호")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis 비밀번호")
    
    # === 외부 서비스 연동 ===
    GATEWAY_URL: str = Field(default="http://localhost:8080", description="Gateway 서비스 URL")
    
    # === API 설정 ===
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 접두사")
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS 허용 도메인")
    
    # === 성능 설정 ===
    REQUEST_TIMEOUT: int = Field(default=30, description="요청 타임아웃 (초)")
    MAX_CONNECTIONS: int = Field(default=100, description="최대 연결 수")
    
    # === Pydantic 설정 ===
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # 추가 설정 허용
    
    # === 유효성 검증 ===
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment must be one of {allowed}')
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f'Log level must be one of {allowed}')
        return v.upper()
    
    @validator('PORT')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    # === 헬퍼 메서드 ===
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.ENVIRONMENT == "development"
    
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.ENVIRONMENT == "production"
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Redis 설정 딕셔너리 반환"""
        return {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB,
            "password": self.REDIS_PASSWORD
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 딕셔너리 반환"""
        return {
            "name": self.APP_NAME,
            "version": self.VERSION,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "host": self.HOST,
            "port": self.PORT
        }

class MLServiceSettings(BaseServiceSettings):
    """ML 기능이 있는 서비스를 위한 확장 설정"""
    
    # === ML 모델 설정 ===
    MODEL_BASE_PATH: Optional[str] = Field(default="/app/shared/models", description="모델 기본 경로")
    MODEL_NAME: Optional[str] = Field(default="test222", description="사용할 모델 이름")
    DISABLE_ML_MODEL: bool = Field(default=False, description="ML 모델 비활성화")
    
    # === Celery 설정 ===
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", description="Celery 브로커 URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", description="Celery 결과 백엔드")
    
    # === 외부 API 설정 ===
    NAVER_CLIENT_ID: Optional[str] = Field(default=None, description="네이버 API 클라이언트 ID")
    NAVER_CLIENT_SECRET: Optional[str] = Field(default=None, description="네이버 API 클라이언트 시크릿")
    
    # === HuggingFace 설정 ===
    HF_HUB_OFFLINE: bool = Field(default=True, description="HuggingFace Hub 오프라인 모드")
    TRANSFORMERS_OFFLINE: bool = Field(default=True, description="Transformers 오프라인 모드")
    
    # === CPU 최적화 설정 ===
    OMP_NUM_THREADS: int = Field(default=2, description="OpenMP 스레드 수")
    TOKENIZERS_PARALLELISM: bool = Field(default=False, description="토크나이저 병렬화")
    
    @validator('MODEL_BASE_PATH')
    def validate_model_path(cls, v):
        if v and not Path(v).exists():
            # 컨테이너 환경에서는 디렉토리 생성 시도하지 않음
            if os.getenv('ENVIRONMENT') == 'production' or os.path.exists('/.dockerenv'):
                # Docker 컨테이너 내부이거나 프로덕션 환경에서는 경고만
                print(f"Info: Model path {v} will be mounted as volume")
            else:
                # 개발 환경에서만 디렉토리 생성 시도
                try:
                    Path(v).mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    print(f"Warning: Cannot create model path {v} - permission denied")
        return v 