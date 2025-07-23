from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class NewsItem:
    """뉴스 아이템 데이터 클래스"""
    title: str
    content: str
    link: str
    published_at: str
    source: str

@dataclass
class SentimentResult:
    """감정 분석 결과 데이터 클래스"""
    label: str
    confidence: float
    raw_label: Optional[str] = None

class NewsServiceInterface(ABC):
    """뉴스 서비스 인터페이스"""
    
    @abstractmethod
    async def search_news(
        self, 
        query: str, 
        display: int = 100,
        start: int = 1,
        sort: str = "sim"
    ) -> List[NewsItem]:
        """뉴스 검색"""
        pass
    
    @abstractmethod
    async def get_news_count(self, query: str) -> int:
        """검색 결과 개수 조회"""
        pass

class MLInferenceInterface(ABC):
    """ML 추론 서비스 인터페이스"""
    
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> SentimentResult:
        """감정 분석"""
        pass
    
    @abstractmethod
    async def analyze_sentiment_batch(self, texts: List[str]) -> List[SentimentResult]:
        """배치 감정 분석"""
        pass
    
    @abstractmethod
    def is_model_loaded(self) -> bool:
        """모델 로드 상태 확인"""
        pass

class CacheServiceInterface(ABC):
    """캐시 서비스 인터페이스"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """캐시 조회"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """캐시 저장"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """캐시 삭제"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """캐시 존재 여부"""
        pass

class AnalysisServiceInterface(ABC):
    """분석 서비스 인터페이스"""
    
    @abstractmethod
    async def analyze_news_with_keywords(
        self, 
        keywords: List[str], 
        company_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """키워드 기반 뉴스 분석"""
        pass
    
    @abstractmethod
    async def analyze_with_combined_keywords(
        self,
        domain_keywords: List[str],
        issue_keywords: List[str],
        company_name: Optional[str] = None,
        max_combinations: int = 5
    ) -> List[Dict[str, Any]]:
        """조합 키워드 기반 분석"""
        pass 