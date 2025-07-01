"""ML 관련 설정 통합 관리"""
import os
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

class ModelType(Enum):
    """모델 타입"""
    CATEGORY = "category"
    SENTIMENT = "sentiment"

@dataclass
class MLModelSettings:
    """ML 모델 관련 설정"""
    models_dir: str = "/app/models"
    model_name: str = "test123"
    max_length: int = 512
    use_fast_tokenizer: bool = True
    torch_dtype_gpu: str = "float16"
    torch_dtype_cpu: str = "float32"
    
    # 기본 라벨 매핑
    default_category_labels: Dict[str, str] = None
    default_sentiment_labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.default_category_labels is None:
            self.default_category_labels = {
                "0": "E", "1": "G", "2": "S", "3": "FIN", "4": "기타"
            }
        if self.default_sentiment_labels is None:
            self.default_sentiment_labels = {
                "0": "긍정", "1": "부정", "2": "중립"
            }
    
    @classmethod
    def from_env(cls) -> "MLModelSettings":
        """환경변수에서 ML 모델 설정 생성"""
        return cls(
            models_dir=os.environ.get("MODELS_DIR", "/app/models"),
            model_name=os.environ.get("MODEL_NAME", "test123")
        )
    
    def get_model_path(self, model_type: ModelType) -> str:
        """모델 경로 반환"""
        return os.path.join(self.models_dir, f"{self.model_name}_{model_type.value}")
    
    def get_label_encoder_path(self, model_type: ModelType) -> str:
        """라벨 인코더 파일 경로 반환"""
        model_path = self.get_model_path(model_type)
        return os.path.join(model_path, "label_encoder.json")

@dataclass
class MLProcessingSettings:
    """ML 처리 관련 설정"""
    batch_size: int = 20
    similarity_threshold: float = 0.75
    chunk_size: int = 50
    max_text_length: int = 200
    
    # 모델 로딩 옵션
    local_files_only: bool = True
    trust_remote_code: bool = False
    use_auth_token: bool = False
    force_download: bool = False
    resume_download: bool = False
    
    @classmethod
    def from_env(cls) -> "MLProcessingSettings":
        """환경변수에서 처리 설정 생성"""
        return cls(
            batch_size=int(os.environ.get("ML_BATCH_SIZE", "20")),
            similarity_threshold=float(os.environ.get("SIMILARITY_THRESHOLD", "0.75")),
            chunk_size=int(os.environ.get("CHUNK_SIZE", "50")),
            max_text_length=int(os.environ.get("MAX_TEXT_LENGTH", "200"))
        )
    
    def get_model_load_options(self, device_type: str) -> Dict[str, Any]:
        """모델 로딩 옵션을 딕셔너리로 변환"""
        options = {
            "local_files_only": self.local_files_only,
            "trust_remote_code": self.trust_remote_code,
            "token": self.use_auth_token,
            "force_download": self.force_download,
            "resume_download": self.resume_download,
        }
        
        # torch_dtype 설정
        if device_type == "cuda":
            try:
                import torch
                options["torch_dtype"] = torch.float16
            except ImportError:
                pass
        else:
            try:
                import torch
                options["torch_dtype"] = torch.float32
            except ImportError:
                pass
        
        # accelerate 패키지가 있는 경우에만 low_cpu_mem_usage 사용
        try:
            import accelerate
            options["low_cpu_mem_usage"] = True
        except ImportError:
            pass
            
        return options

@dataclass
class DashboardSettings:
    """대시보드 관련 설정"""
    monitored_companies: list[str] = None
    analysis_interval_minutes: int = 30
    cache_expire_hours: int = 24
    history_max_count: int = 50
    history_expire_days: int = 7
    
    def __post_init__(self):
        if self.monitored_companies is None:
            self.monitored_companies = ["삼성전자", "LG전자"]
    
    @classmethod
    def from_env(cls) -> "DashboardSettings":
        """환경변수에서 대시보드 설정 생성"""
        companies_env = os.environ.get("MONITORED_COMPANIES")
        companies = companies_env.split(",") if companies_env else None
        
        return cls(
            monitored_companies=companies,
            analysis_interval_minutes=int(os.environ.get("ANALYSIS_INTERVAL_MINUTES", "30")),
            cache_expire_hours=int(os.environ.get("CACHE_EXPIRE_HOURS", "24")),
            history_max_count=int(os.environ.get("HISTORY_MAX_COUNT", "50")),
            history_expire_days=int(os.environ.get("HISTORY_EXPIRE_DAYS", "7"))
        )

# 전역 설정 인스턴스
ml_model_settings = MLModelSettings.from_env()
ml_processing_settings = MLProcessingSettings.from_env()
dashboard_settings = DashboardSettings.from_env() 