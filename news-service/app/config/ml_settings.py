"""ML 관련 설정 통합 관리"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
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
    default_category_labels: Dict[str, str] = field(default_factory=lambda: {
        "0": "E", "1": "G", "2": "S", "3": "FIN", "4": "기타"
    })
    default_sentiment_labels: Dict[str, str] = field(default_factory=lambda: {
        "0": "긍정", "1": "부정", "2": "중립"
    })
    
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
    batch_size: int = 32  # 20 → 32로 증가 (GPU 활용도 극대화)
    similarity_threshold: float = 0.75
    chunk_size: int = 100  # 50 → 100으로 증가 (처리량 증가)
    max_text_length: int = 300  # 200 → 300으로 증가 (더 많은 정보 처리)
    
    # 모델 로딩 옵션
    local_files_only: bool = True
    trust_remote_code: bool = False
    use_auth_token: bool = False
    force_download: bool = False
    resume_download: bool = False
    
    # 성능 최적화 옵션
    use_compiled_model: bool = True  # 모델 컴파일 사용
    use_half_precision: bool = True  # half precision 사용 (GPU 메모리 절약)
    optimize_for_inference: bool = True  # 추론 최적화
    
    @classmethod
    def from_env(cls) -> "MLProcessingSettings":
        """환경변수에서 처리 설정 생성"""
        return cls(
            batch_size=int(os.environ.get("ML_BATCH_SIZE", "32")),
            similarity_threshold=float(os.environ.get("SIMILARITY_THRESHOLD", "0.75")),
            chunk_size=int(os.environ.get("CHUNK_SIZE", "100")),
            max_text_length=int(os.environ.get("MAX_TEXT_LENGTH", "300")),
            use_compiled_model=os.environ.get("USE_COMPILED_MODEL", "true").lower() == "true",
            use_half_precision=os.environ.get("USE_HALF_PRECISION", "true").lower() == "true",
            optimize_for_inference=os.environ.get("OPTIMIZE_FOR_INFERENCE", "true").lower() == "true"
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
        
        # torch_dtype 설정 (성능 최적화)
        if device_type == "cuda" and self.use_half_precision:
            try:
                import torch  # type: ignore
                options["torch_dtype"] = torch.float16  # type: ignore
            except ImportError:
                pass
        else:
            try:
                import torch  # type: ignore
                options["torch_dtype"] = torch.float32  # type: ignore
            except ImportError:
                pass
        
        # accelerate 패키지가 있는 경우에만 low_cpu_mem_usage 사용
        try:
            import accelerate  # type: ignore
            options["low_cpu_mem_usage"] = True
        except ImportError:
            pass
        
        # 추론 최적화
        if self.optimize_for_inference:
            options["use_cache"] = True
            
        return options

@dataclass
class DashboardSettings:
    """대시보드 관련 설정"""
    monitored_companies: list[str] = field(default_factory=lambda: ["삼성전자", "LG전자"])
    analysis_interval_minutes: int = 30
    cache_expire_hours: int = 24
    history_max_count: int = 50
    history_expire_days: int = 7
    
    @classmethod
    def from_env(cls) -> "DashboardSettings":
        """환경변수에서 대시보드 설정 생성"""
        companies_env = os.environ.get("MONITORED_COMPANIES")
        companies = companies_env.split(",") if companies_env else ["삼성전자", "LG전자"]
        
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