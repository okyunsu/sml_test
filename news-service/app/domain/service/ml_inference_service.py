import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from datetime import datetime

# HuggingFace 완전 오프라인 모드 강제 설정
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

logger = logging.getLogger(__name__)

class MLInferenceService:
    """파인튜닝된 모델을 사용한 ML 추론 서비스 (메모리 최적화)"""
    
    def __init__(self):
        # 고정된 외부 모델 경로
        self.models_dir = "/app/models"
        
        # 환경변수에서 모델 이름 가져오기 (기본값: test123)
        self.model_name = os.environ.get("MODEL_NAME", "test123")
        
        logger.info("=== ML 추론 서비스 초기화 시작 ===")
        logger.info(f"모델 디렉토리: {self.models_dir}")
        logger.info(f"사용할 모델 이름: {self.model_name}")
        
        self.category_model = None
        self.category_tokenizer = None
        self.category_label_mapping = None
        self.sentiment_model = None
        self.sentiment_tokenizer = None
        self.sentiment_label_mapping = None
        
        # 디바이스 설정 (메모리 최적화)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # GPU 메모리 최적화 설정
        if torch.cuda.is_available():
            torch.cuda.empty_cache()  # 기존 캐시 정리
            torch.backends.cudnn.benchmark = False  # 메모리 절약
            torch.backends.cudnn.deterministic = True
        
        logger.info(f"ML 추론 서비스 초기화 - 디바이스: {self.device}")
        
        # GPU 정보 출력 (간소화)
        if torch.cuda.is_available():
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"GPU 메모리: {total_memory:.1f} GB")
        else:
            logger.warning("CUDA를 사용할 수 없습니다. CPU 모드로 실행됩니다.")
            
        logger.info(f"사용할 모델: {self.model_name}")
        
        # 모델 디렉토리 존재 확인
        if not os.path.exists(self.models_dir):
            logger.error(f"모델 디렉토리가 존재하지 않습니다: {self.models_dir}")
            raise FileNotFoundError(f"모델 디렉토리를 찾을 수 없습니다: {self.models_dir}")
        
        # 모델 디렉토리 내용 확인
        try:
            model_dirs = os.listdir(self.models_dir)
            logger.info(f"모델 디렉토리 내용: {model_dirs}")
        except Exception as e:
            logger.error(f"모델 디렉토리 읽기 실패: {str(e)}")
        
        # 모델 로드 시도
        logger.info("모델 로드 프로세스 시작")
        self._load_models()
        logger.info("=== ML 추론 서비스 초기화 완료 ===")
    
    def _load_models(self):
        """파인튜닝된 모델들을 로드합니다. (메모리 최적화)"""
        logger.info("=== 모델 로드 시작 ===")
        try:
            # 카테고리 모델 로드
            category_model_path = os.path.join(self.models_dir, f"{self.model_name}_category")
            logger.info(f"카테고리 모델 경로: {category_model_path}")
            
            if os.path.exists(category_model_path):
                logger.info("카테고리 모델 디렉토리 발견, 로드 시작")
                self._load_category_model(category_model_path)
                logger.info("카테고리 모델 로드 성공")
            else:
                logger.warning(f"카테고리 모델을 찾을 수 없습니다: {category_model_path}")
            
            # 감정 모델 로드
            sentiment_model_path = os.path.join(self.models_dir, f"{self.model_name}_sentiment")
            logger.info(f"감정 모델 경로: {sentiment_model_path}")
            
            if os.path.exists(sentiment_model_path):
                logger.info("감정 모델 디렉토리 발견, 로드 시작")
                self._load_sentiment_model(sentiment_model_path)
                logger.info("감정 모델 로드 성공")
            else:
                logger.warning(f"감정 모델을 찾을 수 없습니다: {sentiment_model_path}")
                
            # 모델 로드 결과 요약
            category_loaded = self.category_model is not None
            sentiment_loaded = self.sentiment_model is not None
            logger.info(f"모델 로드 결과 - 카테고리: {'성공' if category_loaded else '실패'}, 감정: {'성공' if sentiment_loaded else '실패'}")
            
            if not category_loaded and not sentiment_loaded:
                logger.error("모든 모델 로드에 실패했습니다. 키워드 기반 분석으로 대체됩니다.")
            elif not category_loaded:
                logger.warning("카테고리 모델 로드 실패. 해당 기능은 키워드 기반으로 대체됩니다.")
            elif not sentiment_loaded:
                logger.warning("감정 모델 로드 실패. 해당 기능은 키워드 기반으로 대체됩니다.")
            else:
                logger.info("모든 모델이 성공적으로 로드되었습니다!")
                
        except Exception as e:
            logger.error(f"모델 로드 중 오류: {str(e)}")
            logger.error(f"오류 타입: {type(e).__name__}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            raise
    
    def _load_category_model(self, model_path: str):
        """카테고리 분류 모델 로드 (메모리 최적화)"""
        logger.info(f"=== 카테고리 모델 로드 시작: {model_path} ===")
        try:
            # 토크나이저 로드 (완전 오프라인 모드)
            logger.info("카테고리 토크나이저 로드 중...")
            self.category_tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True,  # 로컬 파일만 사용
                use_fast=True,  # 빠른 토크나이저 사용
                trust_remote_code=False,  # 원격 코드 실행 금지
                token=False,  # 인증 토큰 사용 안함 (deprecated: use_auth_token)
            )
            logger.info("카테고리 토크나이저 로드 완료")
            
            # 모델 로드 (완전 오프라인 모드)
            logger.info("카테고리 모델 로드 옵션 설정 중...")
            model_kwargs = {
                "local_files_only": True,  # 로컬 파일만 사용
                "torch_dtype": torch.float16 if self.device.type == "cuda" else torch.float32,  # 반정밀도 사용
                "trust_remote_code": False,  # 원격 코드 실행 금지
                "token": False,  # 인증 토큰 사용 안함 (deprecated: use_auth_token)
                "force_download": False,  # 강제 다운로드 금지
                "resume_download": False,  # 재개 다운로드 금지
            }
            
            # accelerate가 있는 경우에만 low_cpu_mem_usage 사용
            try:
                import accelerate
                model_kwargs["low_cpu_mem_usage"] = True
                logger.info("accelerate 패키지 발견, low_cpu_mem_usage 옵션 활성화")
            except ImportError:
                logger.info("accelerate 패키지가 없어 low_cpu_mem_usage 옵션을 사용하지 않습니다")
            
            logger.info(f"모델 로드 옵션: {model_kwargs}")
            logger.info("카테고리 모델 로드 중... (시간이 걸릴 수 있습니다)")
            
            self.category_model = AutoModelForSequenceClassification.from_pretrained(
                model_path,
                **model_kwargs
            )
            logger.info("카테고리 모델 객체 생성 완료")
            
            logger.info(f"모델을 디바이스로 이동 중: {self.device}")
            self.category_model.to(self.device)
            self.category_model.eval()
            logger.info("카테고리 모델 디바이스 이동 및 평가 모드 설정 완료")
            
            # 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("GPU 메모리 캐시 정리 완료")
            
            # 라벨 매핑 로드
            label_encoder_path = os.path.join(model_path, "label_encoder.json")
            logger.info(f"라벨 인코더 파일 확인: {label_encoder_path}")
            
            if os.path.exists(label_encoder_path):
                logger.info("라벨 인코더 파일 발견, 로드 중...")
                with open(label_encoder_path, "r", encoding="utf-8") as f:
                    self.category_label_mapping = json.load(f)
                logger.info(f"라벨 인코더 로드 완료: {self.category_label_mapping}")
            else:
                # 기본 라벨 매핑
                logger.warning("라벨 인코더 파일이 없어 기본 매핑 사용")
                self.category_label_mapping = {
                    "0": "E",
                    "1": "G", 
                    "2": "S",
                    "3": "FIN",
                    "4": "기타"
                }
            
            logger.info(f"카테고리 모델 로드 완료: {model_path}")
            logger.info(f"카테고리 라벨: {self.category_label_mapping}")
            
        except Exception as e:
            logger.error(f"카테고리 모델 로드 실패: {str(e)}")
            logger.error(f"오류 타입: {type(e).__name__}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            raise
    
    def _load_sentiment_model(self, model_path: str):
        """감정 분석 모델 로드 (메모리 최적화)"""
        try:
            # 토크나이저 로드 (완전 오프라인 모드)
            self.sentiment_tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True,  # 로컬 파일만 사용
                use_fast=True,  # 빠른 토크나이저 사용
                trust_remote_code=False,  # 원격 코드 실행 금지
                token=False,  # 인증 토큰 사용 안함 (deprecated: use_auth_token)
            )
            
            # 모델 로드 (완전 오프라인 모드)
            model_kwargs = {
                "local_files_only": True,  # 로컬 파일만 사용
                "torch_dtype": torch.float16 if self.device.type == "cuda" else torch.float32,  # 반정밀도 사용
                "trust_remote_code": False,  # 원격 코드 실행 금지
                "token": False,  # 인증 토큰 사용 안함 (deprecated: use_auth_token)
                "force_download": False,  # 강제 다운로드 금지
                "resume_download": False,  # 재개 다운로드 금지
            }
            
            # accelerate가 있는 경우에만 low_cpu_mem_usage 사용
            try:
                import accelerate
                model_kwargs["low_cpu_mem_usage"] = True
            except ImportError:
                logger.info("accelerate 패키지가 없어 low_cpu_mem_usage 옵션을 사용하지 않습니다")
            
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
                model_path,
                **model_kwargs
            )
            self.sentiment_model.to(self.device)
            self.sentiment_model.eval()
            
            # 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # 라벨 매핑 로드
            label_encoder_path = os.path.join(model_path, "label_encoder.json")
            if os.path.exists(label_encoder_path):
                with open(label_encoder_path, "r", encoding="utf-8") as f:
                    self.sentiment_label_mapping = json.load(f)
            else:
                # 기본 라벨 매핑
                self.sentiment_label_mapping = {
                    "0": "긍정",
                    "1": "부정", 
                    "2": "중립"
                }
            
            logger.info(f"감정 모델 로드 완료: {model_path}")
            logger.info(f"감정 라벨: {self.sentiment_label_mapping}")
            
        except Exception as e:
            logger.error(f"감정 모델 로드 실패: {str(e)}")
            raise
    
    def predict_category(self, text: str) -> Dict[str, Any]:
        """ESG 카테고리 예측"""
        if not self.category_model or not self.category_tokenizer:
            raise ValueError("카테고리 모델이 로드되지 않았습니다")
        
        try:
            # 텍스트 전처리
            inputs = self.category_tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 예측 수행
            with torch.no_grad():
                outputs = self.category_model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
            
            # 결과 매핑
            predicted_label = self.category_label_mapping.get(str(predicted_class), "기타")
            
            # 모든 클래스의 확률 계산
            class_probabilities = {}
            for i, prob in enumerate(probabilities[0].tolist()):
                label = self.category_label_mapping.get(str(i), f"class_{i}")
                class_probabilities[label] = prob
            
            return {
                "predicted_class": predicted_class,
                "predicted_label": predicted_label,
                "confidence": confidence,
                "probabilities": class_probabilities
            }
            
        except Exception as e:
            logger.error(f"카테고리 예측 중 오류: {str(e)}")
            raise
    
    def predict_sentiment(self, text: str) -> Dict[str, Any]:
        """감정 분석 예측"""
        if not self.sentiment_model or not self.sentiment_tokenizer:
            raise ValueError("감정 모델이 로드되지 않았습니다")
        
        try:
            # 텍스트 전처리
            inputs = self.sentiment_tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 예측 수행
            with torch.no_grad():
                outputs = self.sentiment_model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
            
            # 결과 매핑
            predicted_label = self.sentiment_label_mapping.get(str(predicted_class), "중립")
            
            # 모든 클래스의 확률 계산
            class_probabilities = {}
            for i, prob in enumerate(probabilities[0].tolist()):
                label = self.sentiment_label_mapping.get(str(i), f"class_{i}")
                class_probabilities[label] = prob
            
            return {
                "predicted_class": predicted_class,
                "predicted_label": predicted_label,
                "confidence": confidence,
                "probabilities": class_probabilities
            }
            
        except Exception as e:
            logger.error(f"감정 예측 중 오류: {str(e)}")
            raise
    
    def analyze_news_batch(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """뉴스 배치 분석"""
        results = []
        
        for item in news_items:
            try:
                # 텍스트 결합 (제목 + 설명)
                text = f"{item.get('title', '')} {item.get('description', '')}".strip()
                
                if not text:
                    # 빈 텍스트인 경우 기본값
                    result = {
                        **item,
                        "esg_classification": {
                            "category": "기타",
                            "confidence": 0.0,
                            "probabilities": {},
                            "classification_method": "default"
                        },
                        "sentiment_analysis": {
                            "sentiment": "중립",
                            "confidence": 0.0,
                            "probabilities": {},
                            "classification_method": "default"
                        }
                    }
                else:
                    # ML 모델로 분석
                    category_result = self.predict_category(text)
                    sentiment_result = self.predict_sentiment(text)
                    
                    result = {
                        **item,
                        "esg_classification": {
                            "category": category_result["predicted_label"],
                            "confidence": category_result["confidence"],
                            "probabilities": category_result["probabilities"],
                            "classification_method": "fine_tuned_model"
                        },
                        "sentiment_analysis": {
                            "sentiment": sentiment_result["predicted_label"],
                            "confidence": sentiment_result["confidence"],
                            "probabilities": sentiment_result["probabilities"],
                            "classification_method": "fine_tuned_model"
                        }
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"뉴스 항목 분석 중 오류: {str(e)}")
                # 오류 발생 시 기본값으로 처리
                result = {
                    **item,
                    "esg_classification": {
                        "category": "기타",
                        "confidence": 0.0,
                        "probabilities": {},
                        "classification_method": "error_fallback"
                    },
                    "sentiment_analysis": {
                        "sentiment": "중립",
                        "confidence": 0.0,
                        "probabilities": {},
                        "classification_method": "error_fallback"
                    }
                }
                results.append(result)
        
        return results
    
    def is_available(self) -> bool:
        """ML 추론 서비스 사용 가능 여부"""
        return (self.category_model is not None and 
                self.sentiment_model is not None)
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 조회"""
        return {
            "category_model_available": self.category_model is not None,
            "sentiment_model_available": self.sentiment_model is not None,
            "device": str(self.device),
            "category_labels": self.category_label_mapping,
            "sentiment_labels": self.sentiment_label_mapping
        } 