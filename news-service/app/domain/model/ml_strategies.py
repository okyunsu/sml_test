"""분석 전략 패턴"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.config.ml_settings import ml_processing_settings

class ESGAnalysisStrategy(ABC):
    """ESG 분석 전략 추상 클래스"""
    
    @abstractmethod
    async def analyze(self, text: str) -> Dict[str, Any]:
        """ESG 분석 수행"""
        pass

class SentimentAnalysisStrategy(ABC):
    """감정 분석 전략 추상 클래스"""
    
    @abstractmethod
    async def analyze(self, text: str) -> Dict[str, Any]:
        """감정 분석 수행"""
        pass

class KeywordBasedESGStrategy(ESGAnalysisStrategy):
    """키워드 기반 ESG 분석"""
    
    def __init__(self):
        self.esg_keywords = {
            "환경(E)": ["환경", "탄소", "친환경", "재생에너지", "온실가스", "기후변화"],
            "사회(S)": ["사회", "인권", "다양성", "안전", "직원", "고용"],
            "지배구조(G)": ["거버넌스", "윤리", "투명", "컴플라이언스", "이사회"],
            "통합ESG": ["esg", "지속가능", "지속가능성"]
        }
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """키워드 기반 ESG 분석"""
        await asyncio.sleep(0)  # 비동기 처리를 위한 양보
        
        text = text.lower()
        best_category = "기타"
        best_score = 0.0
        matched_keywords = []
        
        for category, keywords in self.esg_keywords.items():
            matches = [keyword for keyword in keywords if keyword in text]
            if matches:
                score = len(matches) / len(keywords)
                if score > best_score:
                    best_score = score
                    best_category = category
                    matched_keywords = matches
        
        return {
            "category": best_category,
            "confidence": min(best_score + 0.4, 1.0),
            "keywords": matched_keywords,
            "method": "keyword_fallback"
        }

class KeywordBasedSentimentStrategy(SentimentAnalysisStrategy):
    """키워드 기반 감정 분석"""
    
    def __init__(self):
        self.positive_keywords = ["성장", "증가", "개선", "성공", "발전", "상승", "호조"]
        self.negative_keywords = ["감소", "하락", "문제", "위험", "손실", "악화", "우려"]
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """키워드 기반 감정 분석"""
        await asyncio.sleep(0)  # 비동기 처리를 위한 양보
        
        text = text.lower()
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text)
        
        if positive_count > negative_count:
            sentiment = "긍정"
            positive_score = 0.7
            negative_score = 0.2
            neutral_score = 0.1
        elif negative_count > positive_count:
            sentiment = "부정"
            positive_score = 0.2
            negative_score = 0.7
            neutral_score = 0.1
        else:
            sentiment = "중립"
            positive_score = 0.3
            negative_score = 0.3
            neutral_score = 0.4
        
        confidence = min((abs(positive_count - negative_count) + 1) * 0.2, 1.0)
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive": positive_score,
            "negative": negative_score,
            "neutral": neutral_score,
            "method": "keyword_fallback"
        }

class MLBasedESGStrategy(ESGAnalysisStrategy):
    """ML 모델 기반 ESG 분석"""
    
    def __init__(self, model, tokenizer, label_mapping, device, max_length=512):
        self.model = model
        self.tokenizer = tokenizer
        self.label_mapping = label_mapping
        self.device = device
        self.max_length = max_length
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """ML 모델 기반 ESG 분석"""
        await asyncio.sleep(0)  # 비동기 처리를 위한 양보
        
        try:
            import torch
            
            # 텍스트 전처리
            inputs = self.tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=self.max_length,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 예측 수행
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
            
            # 결과 매핑
            predicted_label = self.label_mapping.get(str(predicted_class), "기타")
            
            # 모든 클래스의 확률 계산
            class_probabilities = {}
            for i, prob in enumerate(probabilities[0].tolist()):
                label = self.label_mapping.get(str(i), f"class_{i}")
                class_probabilities[label] = prob
            
            return {
                "category": predicted_label,
                "confidence": confidence,
                "probabilities": class_probabilities,
                "method": "fine_tuned_model"
            }
            
        except Exception as e:
            raise Exception(f"ML ESG 분석 실패: {str(e)}")

class MLBasedSentimentStrategy(SentimentAnalysisStrategy):
    """ML 모델 기반 감정 분석"""
    
    def __init__(self, model, tokenizer, label_mapping, device, max_length=512):
        self.model = model
        self.tokenizer = tokenizer
        self.label_mapping = label_mapping
        self.device = device
        self.max_length = max_length
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """ML 모델 기반 감정 분석"""
        await asyncio.sleep(0)  # 비동기 처리를 위한 양보
        
        try:
            import torch
            
            # 텍스트 전처리
            inputs = self.tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=self.max_length,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 예측 수행
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
            
            # 결과 매핑
            predicted_label = self.label_mapping.get(str(predicted_class), "중립")
            
            # 모든 클래스의 확률 계산
            class_probabilities = {}
            for i, prob in enumerate(probabilities[0].tolist()):
                label = self.label_mapping.get(str(i), f"class_{i}")
                class_probabilities[label] = prob
            
            return {
                "sentiment": predicted_label,
                "confidence": confidence,
                "probabilities": class_probabilities,
                "method": "fine_tuned_model"
            }
            
        except Exception as e:
            raise Exception(f"ML 감정 분석 실패: {str(e)}")

class AnalysisContext:
    """분석 컨텍스트"""
    
    def __init__(self, esg_strategy: ESGAnalysisStrategy, sentiment_strategy: SentimentAnalysisStrategy):
        self.esg_strategy = esg_strategy
        self.sentiment_strategy = sentiment_strategy
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """텍스트 분석"""
        esg_task = asyncio.create_task(self.esg_strategy.analyze(text))
        sentiment_task = asyncio.create_task(self.sentiment_strategy.analyze(text))
        
        esg_result, sentiment_result = await asyncio.gather(esg_task, sentiment_task)
        
        return {
            "esg": esg_result,
            "sentiment": sentiment_result
        } 