from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from shared.interfaces.news_service_interface import (
    NewsServiceInterface, MLInferenceInterface, CacheServiceInterface,
    NewsItem, SentimentResult
)

class MockNewsService(NewsServiceInterface):
    """테스트용 Mock 뉴스 서비스"""
    
    def __init__(self, mock_data: Optional[List[NewsItem]] = None):
        self.mock_data = mock_data or self._create_default_mock_data()
        self.call_count = 0
        self.last_query = None
    
    async def search_news(
        self, 
        query: str, 
        display: int = 100,
        start: int = 1,
        sort: str = "sim"
    ) -> List[NewsItem]:
        """Mock 뉴스 검색"""
        self.call_count += 1
        self.last_query = query
        
        # 쿼리에 따라 다른 결과 반환 (테스트 시나리오용)
        if "error" in query.lower():
            raise Exception("Mock API Error")
        
        if "empty" in query.lower():
            return []
        
        # 실제 검색 결과를 시뮬레이션
        filtered_data = [
            item for item in self.mock_data 
            if any(keyword in item.title.lower() for keyword in query.lower().split())
        ]
        
        return filtered_data[:display]
    
    async def get_news_count(self, query: str) -> int:
        """Mock 뉴스 개수 조회"""
        results = await self.search_news(query)
        return len(results)
    
    def _create_default_mock_data(self) -> List[NewsItem]:
        """기본 Mock 데이터 생성"""
        return [
            NewsItem(
                title="두산퓨얼셀 수소연료전지 기술 혁신 발표",
                content="두산퓨얼셀이 새로운 수소연료전지 기술을 공개했다. 이 기술은 기존 대비 효율성이 30% 향상됐다.",
                link="https://example.com/news/1",
                published_at="2024-01-15T10:00:00",
                source="테크뉴스"
            ),
            NewsItem(
                title="LS ELECTRIC 신재생에너지 사업 확장",
                content="LS ELECTRIC이 태양광 발전 시스템 개발에 대규모 투자를 발표했다.",
                link="https://example.com/news/2", 
                published_at="2024-01-15T11:00:00",
                source="에너지뉴스"
            ),
            NewsItem(
                title="탄소중립 정책 변화가 기업에 미치는 영향",
                content="정부의 새로운 탄소중립 정책이 발표되면서 관련 기업들의 대응이 주목받고 있다.",
                link="https://example.com/news/3",
                published_at="2024-01-15T12:00:00",
                source="환경뉴스"
            )
        ]

class MockMLInferenceService(MLInferenceInterface):
    """테스트용 Mock ML 추론 서비스"""
    
    def __init__(self, sentiment_mapping: Optional[Dict[str, str]] = None):
        self.sentiment_mapping = sentiment_mapping or {
            "긍정적": "긍정",
            "부정적": "부정", 
            "중립적": "중립"
        }
        self.model_loaded = True
        self.call_count = 0
    
    async def analyze_sentiment(self, text: str) -> SentimentResult:
        """Mock 감정 분석"""
        self.call_count += 1
        
        if not self.model_loaded:
            raise Exception("Model not loaded")
        
        # 텍스트 내용에 따라 감정 결정 (테스트용)
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["혁신", "성장", "향상", "발전"]):
            return SentimentResult(label="긍정", confidence=0.85, raw_label="LABEL_0")
        elif any(word in text_lower for word in ["문제", "위기", "감소", "실패"]):
            return SentimentResult(label="부정", confidence=0.82, raw_label="LABEL_1")
        else:
            return SentimentResult(label="중립", confidence=0.75, raw_label="LABEL_2")
    
    async def analyze_sentiment_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Mock 배치 감정 분석"""
        results = []
        for text in texts:
            result = await self.analyze_sentiment(text)
            results.append(result)
        return results
    
    def is_model_loaded(self) -> bool:
        """Mock 모델 로드 상태"""
        return self.model_loaded
    
    def set_model_loaded(self, loaded: bool):
        """테스트용 모델 상태 설정"""
        self.model_loaded = loaded

class MockCacheService(CacheServiceInterface):
    """테스트용 Mock 캐시 서비스"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self.call_count = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Mock 캐시 조회"""
        self.call_count += 1
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Mock 캐시 저장"""
        self._cache[key] = value
        # expire_seconds는 Mock에서는 무시 (테스트 단순화)
        return True
    
    async def delete(self, key: str) -> bool:
        """Mock 캐시 삭제"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Mock 캐시 존재 여부"""
        return key in self._cache
    
    def clear_all(self):
        """테스트용 전체 캐시 삭제"""
        self._cache.clear()
    
    def get_cache_size(self) -> int:
        """테스트용 캐시 크기 조회"""
        return len(self._cache)

# 테스트 헬퍼 클래스
class TestDataBuilder:
    """테스트 데이터 빌더"""
    
    @staticmethod
    def create_news_item(
        title: str = "Test News",
        content: str = "Test Content",
        link: str = "https://test.com",
        source: str = "Test Source"
    ) -> NewsItem:
        """테스트용 뉴스 아이템 생성"""
        return NewsItem(
            title=title,
            content=content,
            link=link,
            published_at=datetime.now().isoformat(),
            source=source
        )
    
    @staticmethod
    def create_sentiment_result(
        label: str = "중립",
        confidence: float = 0.8,
        raw_label: str = "LABEL_2"
    ) -> SentimentResult:
        """테스트용 감정 분석 결과 생성"""
        return SentimentResult(
            label=label,
            confidence=confidence,
            raw_label=raw_label
        )
    
    @staticmethod
    def create_multiple_news_items(count: int = 3) -> List[NewsItem]:
        """여러 개의 테스트 뉴스 아이템 생성"""
        return [
            TestDataBuilder.create_news_item(
                title=f"Test News {i+1}",
                content=f"Test Content {i+1}",
                link=f"https://test.com/news/{i+1}"
            )
            for i in range(count)
        ] 