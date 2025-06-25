import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class MLInferenceService:
    """파인튜닝된 모델을 사용한 ML 추론 서비스"""
    
    def __init__(self):
        self.models_dir = "./models"
        self.category_model = None
        self.category_tokenizer = None
        self.category_label_mapping = None
        self.sentiment_model = None
        self.sentiment_tokenizer = None
        self.sentiment_label_mapping = None
        
        # 디바이스 설정
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"ML 추론 서비스 초기화 - 디바이스: {self.device}")
        
        # 모델 로드 시도
        self._load_models()
    
    def _load_models(self):
        """파인튜닝된 모델들을 로드합니다."""
        try:
            # 카테고리 모델 로드
            category_model_path = os.path.join(self.models_dir, "test123_category")
            if os.path.exists(category_model_path):
                self._load_category_model(category_model_path)
            else:
                logger.warning(f"카테고리 모델을 찾을 수 없습니다: {category_model_path}")
            
            # 감정 모델 로드
            sentiment_model_path = os.path.join(self.models_dir, "test123_sentiment")
            if os.path.exists(sentiment_model_path):
                self._load_sentiment_model(sentiment_model_path)
            else:
                logger.warning(f"감정 모델을 찾을 수 없습니다: {sentiment_model_path}")
                
        except Exception as e:
            logger.error(f"모델 로드 중 오류: {str(e)}")
            raise
    
    def _load_category_model(self, model_path: str):
        """카테고리 분류 모델 로드"""
        try:
            # 토크나이저 로드
            self.category_tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # 모델 로드
            self.category_model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.category_model.to(self.device)
            self.category_model.eval()
            
            # 라벨 매핑 로드
            label_encoder_path = os.path.join(model_path, "label_encoder.json")
            if os.path.exists(label_encoder_path):
                with open(label_encoder_path, "r", encoding="utf-8") as f:
                    self.category_label_mapping = json.load(f)
            else:
                # 기본 라벨 매핑
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
            raise
    
    def _load_sentiment_model(self, model_path: str):
        """감정 분석 모델 로드"""
        try:
            # 토크나이저 로드
            self.sentiment_tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # 모델 로드
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.sentiment_model.to(self.device)
            self.sentiment_model.eval()
            
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