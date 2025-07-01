"""모델 로더 전략 패턴"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from app.config.ml_settings import MLModelSettings, ModelType, ml_model_settings

logger = logging.getLogger(__name__)

class ModelLoader(ABC):
    """모델 로더 추상 클래스"""
    
    def __init__(self, config: MLModelSettings):
        self.config = config
    
    @abstractmethod
    def load_model_and_tokenizer(self, model_path: str, device: Any) -> Tuple[Any, Any]:
        """모델과 토크나이저 로드"""
        pass
    
    def load_label_mapping(self, model_path: str, model_type: ModelType) -> Dict[str, str]:
        """라벨 매핑 로드"""
        label_encoder_path = os.path.join(model_path, "label_encoder.json")
        
        if os.path.exists(label_encoder_path):
            try:
                with open(label_encoder_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"라벨 인코더 파일 로드 실패: {e}")
        
        # 기본 라벨 매핑 반환
        if model_type == ModelType.CATEGORY:
            return self.config.default_category_labels
        else:
            return self.config.default_sentiment_labels
    
    def validate_model_path(self, model_path: str) -> bool:
        """모델 경로 유효성 검사"""
        return os.path.exists(model_path)

class HuggingFaceModelLoader(ModelLoader):
    """HuggingFace 모델 로더"""
    
    def load_model_and_tokenizer(self, model_path: str, device: Any) -> Tuple[Any, Any]:
        """HuggingFace 모델과 토크나이저 로드"""
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        
        from app.config.ml_settings import ml_processing_settings
        
        # 토크나이저 로드
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            local_files_only=ml_processing_settings.local_files_only,
            use_fast=self.config.use_fast_tokenizer,
            trust_remote_code=ml_processing_settings.trust_remote_code,
            token=ml_processing_settings.use_auth_token,
        )
        
        # 모델 로드 옵션 생성
        model_kwargs = ml_processing_settings.get_model_load_options(device.type)
        
        # 모델 로드
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            **model_kwargs
        )
        
        # 디바이스로 이동 및 평가 모드 설정
        model.to(device)
        model.eval()
        
        # GPU 메모리 정리
        self._cleanup_gpu_memory()
        
        return model, tokenizer
    
    def _cleanup_gpu_memory(self):
        """GPU 메모리 정리"""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

class ModelLoaderFactory:
    """모델 로더 팩토리"""
    
    @staticmethod
    def create_loader(config: MLModelSettings, loader_type: str = "huggingface") -> ModelLoader:
        """모델 로더 생성"""
        if loader_type.lower() == "huggingface":
            return HuggingFaceModelLoader(config)
        else:
            raise ValueError(f"Unsupported loader type: {loader_type}")

class ModelManager:
    """모델 관리자"""
    
    def __init__(self, config: MLModelSettings):
        self.config = config
        self.loader = ModelLoaderFactory.create_loader(config)
        self._device = None
        
    @property
    def device(self):
        """디바이스 반환"""
        if self._device is None:
            self._device = self._get_device()
        return self._device
    
    def _get_device(self):
        """디바이스 설정"""
        try:
            import torch
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # GPU 메모리 최적화 설정
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.backends.cudnn.benchmark = False
                torch.backends.cudnn.deterministic = True
                
            return device
        except ImportError:
            return "cpu"
    
    def load_model(self, model_type: ModelType) -> Tuple[Any, Any, Dict[str, str]]:
        """모델 로드"""
        model_path = self.config.get_model_path(model_type)
        
        if not self.loader.validate_model_path(model_path):
            raise FileNotFoundError(f"모델을 찾을 수 없습니다: {model_path}")
        
        logger.info(f"{model_type.value} 모델 로드 시작: {model_path}")
        
        try:
            model, tokenizer = self.loader.load_model_and_tokenizer(model_path, self.device)
            label_mapping = self.loader.load_label_mapping(model_path, model_type)
            
            logger.info(f"{model_type.value} 모델 로드 완료")
            return model, tokenizer, label_mapping
            
        except Exception as e:
            logger.error(f"{model_type.value} 모델 로드 실패: {str(e)}")
            raise 