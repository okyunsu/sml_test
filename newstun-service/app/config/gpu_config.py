"""
RTX 2080 최적화 GPU 설정
"""
import torch
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RTX2080Config:
    """RTX 2080 전용 최적화 설정"""
    
    def __init__(self):
        self.device = None
        self.config = {}
        self._initialize_gpu()
    
    def _initialize_gpu(self):
        """GPU 초기화 및 설정"""
        try:
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA가 사용 불가능합니다. GPU 드라이버를 확인하세요.")
            
            # GPU 개수 확인
            gpu_count = torch.cuda.device_count()
            if gpu_count == 0:
                raise RuntimeError("GPU가 감지되지 않았습니다.")
            
            # 첫 번째 GPU 사용
            self.device = torch.device("cuda:0")
            torch.cuda.set_device(0)
            
            # GPU 정보 로깅
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            logger.info(f"GPU 초기화 완료: {gpu_name} ({gpu_memory:.1f}GB)")
            
            # RTX 2080 최적화 설정
            self._setup_rtx2080_config()
            
        except Exception as e:
            logger.error(f"GPU 초기화 실패: {e}")
            raise RuntimeError(f"GPU 초기화 실패: {e}")
    
    def _get_cuda_version(self):
        """CUDA 버전을 안전하게 가져오기"""
        try:
            # torch.version.cuda 속성을 안전하게 가져오기
            version_module = getattr(torch, 'version', None)
            if version_module:
                return getattr(version_module, 'cuda', 'Unknown')
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    def _setup_rtx2080_config(self):
        """RTX 2080 전용 최적화 설정"""
        self.config = {
            # 모델 훈련 설정 (RoBERTa Large 최적화)
            "batch_size": 4,  # RoBERTa Large는 더 작은 배치 크기 필요
            "gradient_accumulation_steps": 4,  # 실질적 배치 크기 16 유지
            "max_length": 512,  # 최대 시퀀스 길이
            "learning_rate": 1e-5,  # RoBERTa Large는 더 낮은 학습률
            "num_epochs": 3,
            "warmup_steps": 100,
            
            # 메모리 최적화
            "fp16": True,  # 혼합 정밀도 활성화
            "dataloader_pin_memory": True,
            "dataloader_num_workers": 2,  # Windows에서 안정적인 워커 수
            "max_memory_usage": 0.8,  # GPU 메모리 80% 사용
            
            # RTX 2080 전용
            "gpu_name": "RTX 2080",
            "cuda_version": "11.8",
            "compute_capability": "7.5",
            
            # 모델 설정
            "model_name": "klue/roberta-large",
            "cache_dir": "./models/cache",
            "output_dir": "./models/trained",
            
            # 로깅 및 저장
            "logging_steps": 10,
            "save_steps": 500,
            "eval_steps": 100,
            "save_total_limit": 3,
            
            # 조기 종료
            "early_stopping_patience": 3,
            "load_best_model_at_end": True,
            "metric_for_best_model": "eval_accuracy",
            "greater_is_better": True,
        }
    
    def get_training_args(self) -> Dict[str, Any]:
        """훈련 인자 반환"""
        return {
            "output_dir": self.config["output_dir"],
            "num_train_epochs": self.config["num_epochs"],
            "per_device_train_batch_size": self.config["batch_size"],
            "per_device_eval_batch_size": self.config["batch_size"],
            "gradient_accumulation_steps": self.config["gradient_accumulation_steps"],
            "learning_rate": self.config["learning_rate"],
            "warmup_steps": self.config["warmup_steps"],
            "logging_steps": self.config["logging_steps"],
            "save_steps": self.config["save_steps"],
            "eval_steps": self.config["eval_steps"],
            "save_total_limit": self.config["save_total_limit"],
            "fp16": self.config["fp16"],
            "dataloader_pin_memory": self.config["dataloader_pin_memory"],
            "dataloader_num_workers": self.config["dataloader_num_workers"],
            "load_best_model_at_end": self.config["load_best_model_at_end"],
            "metric_for_best_model": self.config["metric_for_best_model"],
            "greater_is_better": self.config["greater_is_better"],
            "report_to": [],  # wandb 비활성화
            "remove_unused_columns": False,
        }
    
    def get_model_config(self) -> Dict[str, Any]:
        """모델 설정 반환"""
        return {
            "model_name": self.config["model_name"],
            "cache_dir": self.config["cache_dir"],
            "max_length": self.config["max_length"],
            "device": str(self.device),
        }
    
    def optimize_memory(self):
        """GPU 메모리 최적화"""
        try:
            if torch.cuda.is_available():
                # GPU 캐시 정리
                torch.cuda.empty_cache()
                
                # 메모리 사용량 확인
                allocated = torch.cuda.memory_allocated(0) / 1024**3
                cached = torch.cuda.memory_reserved(0) / 1024**3
                
                logger.info(f"GPU 메모리 - 할당됨: {allocated:.2f}GB, 캐시됨: {cached:.2f}GB")
                
                return {
                    "allocated_gb": round(allocated, 2),
                    "cached_gb": round(cached, 2),
                    "optimized": True
                }
        except Exception as e:
            logger.error(f"메모리 최적화 실패: {e}")
            return {"optimized": False, "error": str(e)}
    
    def get_gpu_status(self) -> Dict[str, Any]:
        """GPU 상태 정보 반환"""
        try:
            if not torch.cuda.is_available():
                return {"available": False, "error": "CUDA 사용 불가"}
            
            device_props = torch.cuda.get_device_properties(0)
            allocated = torch.cuda.memory_allocated(0)
            cached = torch.cuda.memory_reserved(0)
            total = device_props.total_memory
            
            return {
                "available": True,
                "device": str(self.device),
                "name": device_props.name,
                "compute_capability": f"{device_props.major}.{device_props.minor}",
                "total_memory_gb": round(total / 1024**3, 2),
                "allocated_memory_gb": round(allocated / 1024**3, 2),
                "cached_memory_gb": round(cached / 1024**3, 2),
                "free_memory_gb": round((total - allocated) / 1024**3, 2),
                "memory_usage_percent": round((allocated / total) * 100, 1),
                "cuda_version": self._get_cuda_version(),
                "pytorch_version": torch.__version__,
                "config": self.config
            }
        except Exception as e:
            logger.error(f"GPU 상태 확인 실패: {e}")
            return {"available": False, "error": str(e)}
    
    def validate_environment(self) -> Dict[str, Any]:
        """환경 검증"""
        issues = []
        warnings = []
        
        try:
            # CUDA 사용 가능성 체크
            if not torch.cuda.is_available():
                issues.append("CUDA가 사용 불가능합니다")
            
            # GPU 메모리 체크
            if torch.cuda.is_available():
                total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                if total_memory < 6:  # RTX 2080은 8GB
                    warnings.append(f"GPU 메모리가 부족할 수 있습니다: {total_memory:.1f}GB")
            
            # PyTorch 버전 체크
            pytorch_version = torch.__version__
            if not pytorch_version.startswith(('1.', '2.')):
                warnings.append(f"PyTorch 버전 확인 필요: {pytorch_version}")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "gpu_status": self.get_gpu_status()
            }
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"환경 검증 중 오류: {e}"],
                "warnings": [],
                "gpu_status": {"available": False, "error": str(e)}
            }

# 전역 설정 인스턴스
try:
    rtx2080_config = RTX2080Config()
    logger.info("RTX 2080 설정 초기화 완료")
except Exception as e:
    logger.error(f"RTX 2080 설정 초기화 실패: {e}")
    rtx2080_config = None

def get_gpu_config() -> Optional[RTX2080Config]:
    """GPU 설정 인스턴스 반환"""
    return rtx2080_config

def is_gpu_available() -> bool:
    """GPU 사용 가능 여부 확인"""
    return rtx2080_config is not None and torch.cuda.is_available() 