"""분석 전략 패턴 - 배치 처리 최적화"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.config.ml_settings import ml_processing_settings

class ESGAnalysisStrategy(ABC):
    """ESG 분석 전략 추상 클래스"""
    
    @abstractmethod
    async def analyze(self, text: str) -> Dict[str, Any]:
        """단일 텍스트 ESG 분석"""
        pass
    
    @abstractmethod
    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """배치 텍스트 ESG 분석"""
        pass

class SentimentAnalysisStrategy(ABC):
    """감정 분석 전략 추상 클래스"""
    
    @abstractmethod
    async def analyze(self, text: str) -> Dict[str, Any]:
        """단일 텍스트 감정 분석"""
        pass
    
    @abstractmethod
    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """배치 텍스트 감정 분석"""
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
    
    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """배치 키워드 기반 ESG 분석"""
        await asyncio.sleep(0)
        
        results = []
        for text in texts:
            result = await self.analyze(text)
            results.append(result)
        
        return results

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
    
    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """배치 키워드 기반 감정 분석"""
        await asyncio.sleep(0)
        
        results = []
        for text in texts:
            result = await self.analyze(text)
            results.append(result)
        
        return results

class MLBasedESGStrategy(ESGAnalysisStrategy):
    """ML 모델 기반 ESG 분석 - 배치 최적화"""
    
    def __init__(self, model, tokenizer, label_mapping, device, max_length=512):
        self.model = model
        self.tokenizer = tokenizer
        self.label_mapping = label_mapping
        self.device = device
        self.max_length = max_length
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """단일 텍스트 ML 기반 ESG 분석"""
        batch_results = await self.analyze_batch([text])
        return batch_results[0] if batch_results else self._get_default_result()
    
    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """배치 ML 기반 ESG 분석 - 핵심 최적화"""
        await asyncio.sleep(0)  # 비동기 처리를 위한 양보
        
        if not texts:
            return []
        
        try:
            import torch  # type: ignore
            
            # 🚀 배치 토크나이징 (한 번에 모든 텍스트 처리)
            inputs = self.tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=self.max_length,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 🚀 배치 예측 (한 번에 모든 예측 수행)
            with torch.no_grad():  # type: ignore
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)  # type: ignore
                predicted_classes = torch.argmax(probabilities, dim=-1)  # type: ignore
                confidences = torch.max(probabilities, dim=-1)[0]  # type: ignore
            
            # 결과 변환
            results = []
            for i in range(len(texts)):
                predicted_class = predicted_classes[i].item()
                confidence = confidences[i].item()
                predicted_label = self.label_mapping.get(str(predicted_class), "기타")
                
                # 모든 클래스의 확률 계산
                class_probabilities = {}
                for j, prob in enumerate(probabilities[i].tolist()):
                    label = self.label_mapping.get(str(j), f"class_{j}")
                    class_probabilities[label] = prob
                
                results.append({
                    "category": predicted_label,
                    "confidence": confidence,
                    "probabilities": class_probabilities,
                    "method": "fine_tuned_model_batch"
                })
            
            return results
            
        except Exception as e:
            print(f"❌ ML ESG 배치 분석 실패: {str(e)}")
            # 실패 시 기본 결과 반환
            return [self._get_default_result() for _ in texts]
    
    def _get_default_result(self) -> Dict[str, Any]:
        """기본 결과"""
        return {
            "category": "기타",
            "confidence": 0.0,
            "probabilities": {},
            "method": "error_fallback"
        }

class MLBasedSentimentStrategy(SentimentAnalysisStrategy):
    """ML 모델 기반 감정 분석 - 배치 최적화"""
    
    def __init__(self, model, tokenizer, label_mapping, device, max_length=512):
        self.model = model
        self.tokenizer = tokenizer
        self.label_mapping = label_mapping
        self.device = device
        self.max_length = max_length
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """단일 텍스트 ML 기반 감정 분석"""
        batch_results = await self.analyze_batch([text])
        return batch_results[0] if batch_results else self._get_default_result()
    
    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """배치 ML 기반 감정 분석 - 핵심 최적화"""
        await asyncio.sleep(0)  # 비동기 처리를 위한 양보
        
        if not texts:
            return []
        
        try:
            import torch  # type: ignore
            
            # 🚀 배치 토크나이징 (한 번에 모든 텍스트 처리)
            inputs = self.tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=self.max_length,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 🚀 배치 예측 (한 번에 모든 예측 수행)
            with torch.no_grad():  # type: ignore
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)  # type: ignore
                predicted_classes = torch.argmax(probabilities, dim=-1)  # type: ignore
                confidences = torch.max(probabilities, dim=-1)[0]  # type: ignore
            
            # 결과 변환
            results = []
            for i in range(len(texts)):
                predicted_class = predicted_classes[i].item()
                confidence = confidences[i].item()
                predicted_label = self.label_mapping.get(str(predicted_class), "중립")
                
                # 모든 클래스의 확률 계산
                class_probabilities = {}
                for j, prob in enumerate(probabilities[i].tolist()):
                    label = self.label_mapping.get(str(j), f"class_{j}")
                    class_probabilities[label] = prob
                
                results.append({
                    "sentiment": predicted_label,
                    "confidence": confidence,
                    "probabilities": class_probabilities,
                    "method": "fine_tuned_model_batch"
                })
            
            return results
            
        except Exception as e:
            print(f"❌ ML 감정 배치 분석 실패: {str(e)}")
            # 실패 시 기본 결과 반환
            return [self._get_default_result() for _ in texts]
    
    def _get_default_result(self) -> Dict[str, Any]:
        """기본 결과"""
        return {
            "sentiment": "중립",
            "confidence": 0.0,
            "probabilities": {},
            "method": "error_fallback"
        }

class AnalysisContext:
    """분석 컨텍스트 - 배치 처리 최적화"""
    
    def __init__(self, esg_strategy: ESGAnalysisStrategy, sentiment_strategy: SentimentAnalysisStrategy):
        self.esg_strategy = esg_strategy
        self.sentiment_strategy = sentiment_strategy
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """단일 텍스트 분석"""
        batch_results = await self.analyze_batch([text])
        return batch_results[0] if batch_results else self._get_default_result()
    
    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """배치 텍스트 분석 - 🚀 핵심 최적화"""
        if not texts:
            return []
        
        print(f"🚀 배치 분석 시작: {len(texts)}개 텍스트")
        
        # ESG와 감정 분석을 병렬로 배치 처리
        esg_task = asyncio.create_task(self.esg_strategy.analyze_batch(texts))
        sentiment_task = asyncio.create_task(self.sentiment_strategy.analyze_batch(texts))
        
        esg_results, sentiment_results = await asyncio.gather(esg_task, sentiment_task)
        
        # 결과 결합
        combined_results = []
        for i in range(len(texts)):
            esg_result = esg_results[i] if i < len(esg_results) else self._get_default_esg()
            sentiment_result = sentiment_results[i] if i < len(sentiment_results) else self._get_default_sentiment()
            
            combined_results.append({
                "esg": esg_result,
                "sentiment": sentiment_result
            })
        
        print(f"✅ 배치 분석 완료: {len(combined_results)}개 결과")
        return combined_results
    
    def _get_default_result(self) -> Dict[str, Any]:
        """기본 결과"""
        return {
            "esg": self._get_default_esg(),
            "sentiment": self._get_default_sentiment()
        }
    
    def _get_default_esg(self) -> Dict[str, Any]:
        """기본 ESG 결과"""
        return {
            "category": "기타",
            "confidence": 0.0,
            "probabilities": {},
            "method": "default"
        }
    
    def _get_default_sentiment(self) -> Dict[str, Any]:
        """기본 감정 결과"""
        return {
            "sentiment": "중립",
            "confidence": 0.0,
            "probabilities": {},
            "method": "default"
        } 