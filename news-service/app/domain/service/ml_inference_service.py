import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from datetime import datetime

# HuggingFace 완전 오프라인 모드 강제 설정
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from app.config.ml_settings import ModelType, ml_model_settings
from app.domain.model.ml_loader import ModelManager
from app.domain.model.ml_strategies import (
    AnalysisContext, MLBasedESGStrategy, MLBasedSentimentStrategy,
    KeywordBasedESGStrategy, KeywordBasedSentimentStrategy
)

logger = logging.getLogger(__name__)

class MLInferenceService:
    """파인튜닝된 모델을 사용한 ML 추론 서비스 (리팩토링 완료)"""
    
    def __init__(self):
        logger.info("=== ML 추론 서비스 초기화 시작 ===")
        
        # 설정 및 모델 관리자 초기화
        self.config = ml_model_settings
        self.model_manager = ModelManager(self.config)
        
        # 모델 및 분석 전략
        self.category_model = None
        self.category_tokenizer = None
        self.category_label_mapping = None
        self.sentiment_model = None
        self.sentiment_tokenizer = None
        self.sentiment_label_mapping = None
        self.analysis_context = None
        
        # 타임아웃 설정 (초)
        self.analysis_timeout = 30  # 30초 타임아웃
        self.model_load_timeout = 60  # 모델 로딩 60초 타임아웃
        
        self._log_initialization_info()
        self._validate_models_directory()
        self._load_models()
        self._setup_analysis_strategies()
        
        logger.info("=== ML 추론 서비스 초기화 완료 ===")
    
    def _log_initialization_info(self):
        """초기화 정보 로깅"""
        logger.info(f"모델 디렉토리: {self.config.models_dir}")
        logger.info(f"사용할 모델 이름: {self.config.model_name}")
        logger.info(f"분석 타임아웃: {self.analysis_timeout}초")
        logger.info(f"ML 추론 서비스 초기화 - 디바이스: {self.model_manager.device}")
        
        # GPU 정보 출력
        self._log_device_info()
    
    def _log_device_info(self):
        """디바이스 정보 로깅"""
        try:
            import torch
            cuda_module = getattr(torch, 'cuda', None)
            if cuda_module and cuda_module.is_available():
                logger.info(f"GPU: {cuda_module.get_device_name(0)}")
                total_memory = cuda_module.get_device_properties(0).total_memory / 1024**3
                logger.info(f"GPU 메모리: {total_memory:.1f} GB")
            else:
                logger.warning("CUDA를 사용할 수 없습니다. CPU 모드로 실행됩니다.")
        except (ImportError, AttributeError):
            logger.info("PyTorch CUDA가 사용할 수 없습니다.")
    
    def _validate_models_directory(self):
        """모델 디렉토리 유효성 검사"""
        if not os.path.exists(self.config.models_dir):
            logger.error(f"모델 디렉토리가 존재하지 않습니다: {self.config.models_dir}")
            raise FileNotFoundError(f"모델 디렉토리를 찾을 수 없습니다: {self.config.models_dir}")
        
        try:
            model_dirs = os.listdir(self.config.models_dir)
            logger.info(f"모델 디렉토리 내용: {model_dirs}")
        except Exception as e:
            logger.error(f"모델 디렉토리 읽기 실패: {str(e)}")
            raise
    
    def _load_models(self):
        """모델들을 로드합니다"""
        logger.info("=== 모델 로드 시작 ===")
        
        try:
            # 카테고리 모델 로드
            self._load_model_safely(ModelType.CATEGORY)
            
            # 감정 모델 로드  
            self._load_model_safely(ModelType.SENTIMENT)
            
            self._log_model_load_results()
            
        except Exception as e:
            logger.error(f"모델 로드 중 오류: {str(e)}")
            logger.error(f"오류 타입: {type(e).__name__}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            raise
    
    def _load_model_safely(self, model_type: ModelType):
        """안전한 모델 로드 (Windows 호환)"""
        try:
            model_path = self.config.get_model_path(model_type)
            logger.info(f"{model_type.value} 모델 경로: {model_path}")
            
            if os.path.exists(model_path):
                logger.info(f"{model_type.value} 모델 디렉토리 발견, 로드 시작")
                
                # 모델 로드 시도
                try:
                    model, tokenizer, label_mapping = self.model_manager.load_model(model_type)
                    
                    if model_type == ModelType.CATEGORY:
                        self.category_model = model
                        self.category_tokenizer = tokenizer
                        self.category_label_mapping = label_mapping
                    else:
                        self.sentiment_model = model
                        self.sentiment_tokenizer = tokenizer
                        self.sentiment_label_mapping = label_mapping
                    
                    logger.info(f"{model_type.value} 모델 로드 성공")
                    
                except Exception as e:
                    logger.error(f"{model_type.value} 모델 로드 중 예외: {str(e)}")
                    
            else:
                logger.warning(f"{model_type.value} 모델을 찾을 수 없습니다: {model_path}")
                
        except Exception as e:
            logger.error(f"{model_type.value} 모델 로드 실패: {str(e)}")
            # 개별 모델 로드 실패는 전체 서비스를 중단시키지 않음
    
    def _log_model_load_results(self):
        """모델 로드 결과 로깅"""
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
    
    def _setup_analysis_strategies(self):
        """분석 전략 설정"""
        logger.info("=== 분석 전략 설정 시작 ===")
        
        try:
            # ESG 분석 전략
            if self.category_model and self.category_tokenizer:
                logger.info("ML 기반 ESG 분석 전략 사용")
                esg_strategy = MLBasedESGStrategy(
                    self.category_model,
                    self.category_tokenizer,
                    self.category_label_mapping,
                    self.model_manager.device,
                    self.config.max_length
                )
            else:
                logger.info("키워드 기반 ESG 분석 전략 사용")
                esg_strategy = KeywordBasedESGStrategy()
            
            # 감정 분석 전략
            if self.sentiment_model and self.sentiment_tokenizer:
                logger.info("ML 기반 감정 분석 전략 사용")
                sentiment_strategy = MLBasedSentimentStrategy(
                    self.sentiment_model,
                    self.sentiment_tokenizer,
                    self.sentiment_label_mapping,
                    self.model_manager.device,
                    self.config.max_length
                )
            else:
                logger.info("키워드 기반 감정 분석 전략 사용")
                sentiment_strategy = KeywordBasedSentimentStrategy()
            
            self.analysis_context = AnalysisContext(esg_strategy, sentiment_strategy)
            logger.info("✅ 분석 전략 설정 완료")
            
        except Exception as e:
            logger.error(f"❌ 분석 전략 설정 실패: {str(e)}")
            # 폴백으로 키워드 기반 전략만 사용
            try:
                logger.info("🔄 폴백으로 키워드 기반 전략 설정")
                esg_strategy = KeywordBasedESGStrategy()
                sentiment_strategy = KeywordBasedSentimentStrategy()
                self.analysis_context = AnalysisContext(esg_strategy, sentiment_strategy)
                logger.info("✅ 폴백 전략 설정 완료")
            except Exception as fallback_error:
                logger.error(f"❌ 폴백 전략 설정도 실패: {str(fallback_error)}")
                self.analysis_context = None
    
    async def predict_category(self, text: str) -> Dict[str, Any]:
        """ESG 카테고리 예측"""
        if not self.analysis_context:
            raise ValueError("분석 컨텍스트가 초기화되지 않았습니다")
        
        try:
            result = await self.analysis_context.esg_strategy.analyze(text)
            return {
                "predicted_class": 0,  # 호환성을 위해 유지
                "predicted_label": result["category"],
                "confidence": result["confidence"],
                "probabilities": result.get("probabilities", {}),
                "classification_method": result["method"]
            }
        except Exception as e:
            logger.error(f"카테고리 예측 중 오류: {str(e)}")
            raise
    
    async def predict_sentiment(self, text: str) -> Dict[str, Any]:
        """감정 분석 예측"""
        if not self.analysis_context:
            raise ValueError("분석 컨텍스트가 초기화되지 않았습니다")
        
        try:
            result = await self.analysis_context.sentiment_strategy.analyze(text)
            return {
                "predicted_class": 0,  # 호환성을 위해 유지
                "predicted_label": result["sentiment"],
                "confidence": result["confidence"],
                "probabilities": result.get("probabilities", {}),
                "classification_method": result["method"]
            }
        except Exception as e:
            logger.error(f"감정 예측 중 오류: {str(e)}")
            raise
    
    async def analyze_news_batch(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """뉴스 배치 분석 (타임아웃 적용)"""
        logger.info(f"뉴스 배치 분석 시작: {len(news_items)}개 아이템")
        results = []
        
        for i, item in enumerate(news_items):
            try:
                logger.info(f"뉴스 아이템 {i+1}/{len(news_items)} 분석 시작")
                
                # 타임아웃을 적용하여 분석 수행
                result = await asyncio.wait_for(
                    self._analyze_single_news_item(item),
                    timeout=self.analysis_timeout
                )
                results.append(result)
                logger.info(f"뉴스 아이템 {i+1}/{len(news_items)} 분석 완료")
                
            except asyncio.TimeoutError:
                logger.error(f"뉴스 아이템 {i+1}/{len(news_items)} 분석 타임아웃")
                result = self._create_error_fallback_result(item)
                results.append(result)
                
            except Exception as e:
                logger.error(f"뉴스 아이템 {i+1}/{len(news_items)} 분석 중 오류: {str(e)}")
                result = self._create_error_fallback_result(item)
                results.append(result)
        
        logger.info(f"뉴스 배치 분석 완료: {len(results)}개 결과")
        return results
    
    async def _analyze_single_news_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """단일 뉴스 아이템 분석 (타임아웃 및 예외 처리 강화)"""
        text = self._combine_news_text(item)
        
        if not text or not self.analysis_context:
            logger.warning("텍스트가 없거나 분석 컨텍스트가 없음, 기본 결과 반환")
            return self._create_default_result(item)
        
        try:
            # 분석 수행 (타임아웃 적용)
            analysis_result = await asyncio.wait_for(
                self.analysis_context.analyze_text(text),
                timeout=self.analysis_timeout
            )
            
            return {
                **item,
                "esg_classification": {
                    "category": analysis_result["esg"]["category"],
                    "confidence": analysis_result["esg"]["confidence"],
                    "probabilities": analysis_result["esg"].get("probabilities", {}),
                    "classification_method": analysis_result["esg"]["method"]
                },
                "sentiment_analysis": {
                    "sentiment": analysis_result["sentiment"]["sentiment"],
                    "confidence": analysis_result["sentiment"]["confidence"],
                    "probabilities": analysis_result["sentiment"].get("probabilities", {}),
                    "classification_method": analysis_result["sentiment"]["method"]
                }
            }
            
        except asyncio.TimeoutError:
            logger.error("분석 타임아웃, 기본 결과 반환")
            return self._create_timeout_fallback_result(item)
            
        except Exception as e:
            logger.error(f"분석 중 예외 발생: {str(e)}")
            return self._create_error_fallback_result(item)
    
    def _combine_news_text(self, item: Dict[str, Any]) -> str:
        """뉴스 텍스트 결합"""
        title = item.get('title', '')
        description = item.get('description', '')
        return f"{title} {description}".strip()
    
    def _create_default_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """기본 결과 생성"""
        return {
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
    
    def _create_error_fallback_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """오류 시 폴백 결과 생성"""
        return {
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
    
    def _create_timeout_fallback_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """타임아웃 시 폴백 결과 생성"""
        return {
            **item,
            "esg_classification": {
                "category": "기타",
                "confidence": 0.0,
                "probabilities": {},
                "classification_method": "timeout_fallback"
            },
            "sentiment_analysis": {
                "sentiment": "중립",
                "confidence": 0.0,
                "probabilities": {},
                "classification_method": "timeout_fallback"
            }
        }
    
    def is_available(self) -> bool:
        """ML 추론 서비스 사용 가능 여부"""
        return (
            self.analysis_context is not None and
            hasattr(self.analysis_context, 'esg_strategy') and
            hasattr(self.analysis_context, 'sentiment_strategy')
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 조회"""
        return {
            "category_model_available": self.category_model is not None,
            "sentiment_model_available": self.sentiment_model is not None,
            "device": str(self.model_manager.device),
            "category_labels": self.category_label_mapping,
            "sentiment_labels": self.sentiment_label_mapping,
            "config": {
                "models_dir": self.config.models_dir,
                "model_name": self.config.model_name,
                "max_length": self.config.max_length
            }
        } 