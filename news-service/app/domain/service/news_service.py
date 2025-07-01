"""리팩토링된 뉴스 서비스"""
import re
import html
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher

from app.config.settings import settings
from app.domain.model.news_dto import (
    NewsSearchRequest, NewsSearchResponse, NewsItem, 
    TrendingKeywordsResponse, NewsAnalysisRequest
)
from app.core.http_client import HttpClientManager, HttpClientConfig
from app.config.ml_settings import ml_processing_settings

class NewsServiceError(Exception):
    """뉴스 서비스 도메인 예외"""
    pass

class NewsAPIError(NewsServiceError):
    """뉴스 API 관련 예외"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class TextProcessor:
    """텍스트 처리 유틸리티"""
    
    @staticmethod
    def clean_html_text(text: str) -> str:
        """HTML 태그 및 특수문자 정제"""
        if not text:
            return ""
        
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        
        replacements = {
            '&quot;': '"', '&apos;': "'", '&amp;': '&',
            '&lt;': '<', '&gt;': '>'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """텍스트 정규화"""
        if not text:
            return ""
        
        normalized = re.sub(r'[^\w\s가-힣]', ' ', text)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip().lower()

class SimilarityCalculator:
    """유사도 계산 유틸리티"""
    
    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도 계산"""
        if not text1 or not text2:
            return 0.0
        
        text1_truncated = text1[:ml_processing_settings.max_text_length]
        text2_truncated = text2[:ml_processing_settings.max_text_length]
        
        return SequenceMatcher(None, text1_truncated, text2_truncated).ratio()
    
    @staticmethod
    def calculate_news_similarity(item1: NewsItem, item2: NewsItem) -> float:
        """두 뉴스 아이템 간의 유사도 계산"""
        title_similarity = SimilarityCalculator.calculate_text_similarity(
            TextProcessor.normalize_text(item1.title),
            TextProcessor.normalize_text(item2.title)
        )
        
        desc_similarity = SimilarityCalculator.calculate_text_similarity(
            TextProcessor.normalize_text(item1.description),
            TextProcessor.normalize_text(item2.description)
        )
        
        return (title_similarity * 0.7) + (desc_similarity * 0.3)

class DeduplicationProcessor:
    """중복 제거 처리기"""
    
    def __init__(self, similarity_threshold: float = ml_processing_settings.similarity_threshold):
        self.similarity_threshold = similarity_threshold
    
    async def remove_duplicates(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """중복 제거 비동기 처리"""
        if not news_items:
            return []
        
        if len(news_items) > 100:
            return await self._remove_duplicates_large_dataset(news_items)
        else:
            return await self._remove_duplicates_small_dataset(news_items)
    
    async def _remove_duplicates_small_dataset(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """소규모 데이터셋 중복 제거"""
        await asyncio.sleep(0)  # 다른 코루틴에게 제어권 양보
        return self._remove_duplicates_sync(news_items)
    
    async def _remove_duplicates_large_dataset(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """대규모 데이터셋 중복 제거 (병렬 처리)"""
        chunks = self._create_chunks(news_items, ml_processing_settings.chunk_size)
        
        # 각 청크를 병렬로 처리
        tasks = [
            asyncio.create_task(self._process_duplicate_chunk(chunk))
            for chunk in chunks
        ]
        
        chunk_results = await asyncio.gather(*tasks)
        
        # 청크 결과들을 병합하고 최종 중복 제거
        all_items = []
        for chunk_result in chunk_results:
            all_items.extend(chunk_result)
        
        return await self._remove_duplicates_small_dataset(all_items)
    
    def _create_chunks(self, items: List[NewsItem], chunk_size: int) -> List[List[NewsItem]]:
        """아이템을 청크로 나누기"""
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    async def _process_duplicate_chunk(self, chunk: List[NewsItem]) -> List[NewsItem]:
        """중복 제거 청크 처리"""
        await asyncio.sleep(0)
        return self._remove_duplicates_sync(chunk)
    
    def _remove_duplicates_sync(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """동기 중복 제거"""
        unique_news = []
        processed_indices = set()
        
        for i, current_item in enumerate(news_items):
            if i in processed_indices:
                continue
                
            similar_items = [current_item]
            
            for j, compare_item in enumerate(news_items[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                    
                similarity = SimilarityCalculator.calculate_news_similarity(current_item, compare_item)
                
                if similarity >= self.similarity_threshold:
                    similar_items.append(compare_item)
                    processed_indices.add(j)
            
            # 대표 뉴스 선택
            representative = max(similar_items, key=lambda x: len(x.description))
            representative.mention_count = len(similar_items)
            representative.similarity_score = 1.0
            
            unique_news.append(representative)
            processed_indices.add(i)
        
        # 언급 횟수 순으로 정렬
        unique_news.sort(key=lambda x: x.mention_count, reverse=True)
        return unique_news

class NaverAPIClient:
    """네이버 API 클라이언트"""
    
    def __init__(self, client_id: str, client_secret: str, search_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.search_url = search_url
        self.http_manager = HttpClientManager(HttpClientConfig())
    
    async def search_news(self, search_request: NewsSearchRequest) -> Dict[str, Any]:
        """네이버 뉴스 검색"""
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        
        params = {
            "query": search_request.query,
            "display": search_request.display,
            "start": search_request.start,
            "sort": search_request.sort
        }
        
        async with self.http_manager.get_client(headers) as client:
            response = await client.get(
                self.search_url,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def get_api_error_message(status_code: int) -> str:
        """API 에러 코드에 따른 메시지 반환"""
        error_messages = {
            400: "잘못된 요청 파라미터입니다.",
            401: "네이버 API 인증에 실패했습니다.",
            429: "API 호출 한도를 초과했습니다.",
        }
        return error_messages.get(status_code, f"네이버 API 호출 중 오류가 발생했습니다: {status_code}")

class NewsItemProcessor:
    """뉴스 아이템 처리기"""
    
    @staticmethod
    def create_news_item(item: Dict[str, Any]) -> NewsItem:
        """뉴스 아이템 생성"""
        return NewsItem(
            title=TextProcessor.clean_html_text(item.get("title", "")),
            original_link=item.get("originallink", ""),
            link=item.get("link", ""),
            description=TextProcessor.clean_html_text(item.get("description", "")),
            pub_date=item.get("pubDate", ""),
            mention_count=1,
            similarity_score=None
        )
    
    @staticmethod
    async def process_news_items(raw_items: List[Dict[str, Any]]) -> List[NewsItem]:
        """뉴스 아이템들을 비동기로 처리"""
        # CPU 집약적 작업을 위한 배치 처리
        batches = [raw_items[i:i + ml_processing_settings.batch_size]
                   for i in range(0, len(raw_items), ml_processing_settings.batch_size)]
        
        tasks = [
            asyncio.create_task(NewsItemProcessor._process_news_batch(batch))
            for batch in batches
        ]
        
        batch_results = await asyncio.gather(*tasks)
        
        # 결과 병합
        cleaned_items = []
        for batch_result in batch_results:
            cleaned_items.extend(batch_result)
        
        return cleaned_items
    
    @staticmethod
    async def _process_news_batch(batch: List[Dict[str, Any]]) -> List[NewsItem]:
        """뉴스 배치 처리"""
        await asyncio.sleep(0)  # I/O 블로킹 방지
        return [NewsItemProcessor.create_news_item(item) for item in batch]

class NewsService:
    """뉴스 검색 서비스 - 리팩토링 완료"""
    
    def __init__(self):
        # API 클라이언트 초기화
        self._validate_api_credentials()
        self.api_client = NaverAPIClient(
            settings.naver_client_id,
            settings.naver_client_secret,
            settings.naver_search_url
        )
        
        # 처리기들 초기화
        self.dedup_processor = DeduplicationProcessor()
        
    def _validate_api_credentials(self):
        """API 자격 증명 검증"""
        if not settings.naver_client_id or not settings.naver_client_secret:
            raise NewsServiceError("네이버 API 클라이언트 ID와 시크릿이 설정되지 않았습니다.")
    
    async def search_news(self, search_request: NewsSearchRequest) -> NewsSearchResponse:
        """뉴스 검색 실행"""
        try:
            # 네이버 API 호출
            response_data = await self.api_client.search_news(search_request)
            
            # 응답 데이터 처리
            raw_items = response_data.get("items", [])
            if not raw_items:
                return self._create_empty_response(search_request, response_data)
            
            # 데이터 정제를 비동기로 처리
            cleaned_items = await NewsItemProcessor.process_news_items(raw_items)
            original_count = len(cleaned_items)
            
            # 중복 제거 처리
            if search_request.remove_duplicates:
                self.dedup_processor.similarity_threshold = search_request.similarity_threshold
                deduplicated_items = await self.dedup_processor.remove_duplicates(cleaned_items)
                duplicates_removed = original_count - len(deduplicated_items)
            else:
                deduplicated_items = cleaned_items
                duplicates_removed = 0
            
            return NewsSearchResponse(
                last_build_date=response_data.get("lastBuildDate", ""),
                total=response_data.get("total", 0),
                start=response_data.get("start", search_request.start),
                display=response_data.get("display", search_request.display),
                items=deduplicated_items,
                original_count=original_count,
                duplicates_removed=duplicates_removed,
                deduplication_enabled=search_request.remove_duplicates
            )
            
        except Exception as e:
            self._handle_api_error(e)
            # 이 라인은 절대 실행되지 않지만 타입 체커를 위해 추가
            return self._create_empty_response(search_request, {})
    
    def _handle_api_error(self, error: Exception):
        """API 에러 처리"""
        import httpx
        
        if isinstance(error, httpx.HTTPStatusError):
            raise NewsAPIError(
                self.api_client.get_api_error_message(error.response.status_code),
                error.response.status_code
            )
        elif isinstance(error, httpx.RequestError):
            raise NewsAPIError(f"네트워크 오류가 발생했습니다: {str(error)}")
        else:
            raise NewsServiceError(f"뉴스 검색 중 오류가 발생했습니다: {str(error)}")
    
    def _create_empty_response(self, search_request: NewsSearchRequest, response_data: Dict[str, Any]) -> NewsSearchResponse:
        """빈 응답 생성"""
        return NewsSearchResponse(
            last_build_date=response_data.get("lastBuildDate", ""),
            total=0,
            start=search_request.start,
            display=search_request.display,
            items=[],
            original_count=0,
            duplicates_removed=0,
            deduplication_enabled=search_request.remove_duplicates
        )
    
    async def get_trending_keywords(self) -> TrendingKeywordsResponse:
        """한국 주요 기업 키워드 조회"""
        await asyncio.sleep(0)  # 다른 코루틴에게 제어권 양보
        
        company_keywords = [
            "삼성전자", "SK하이닉스", "LG화학", "NAVER", "카카오",
            "현대자동차", "기아", "POSCO", "LG전자", "삼성SDI",
            "현대모비스", "셀트리온", "KB금융", "신한지주", "하나금융지주"
        ]
        
        return TrendingKeywordsResponse(
            keywords=company_keywords,
            category="한국 주요 기업",
            last_updated="2024-12-25T10:30:00Z"
        )
    
    def create_ml_analysis_request(self, news_response: NewsSearchResponse) -> NewsAnalysisRequest:
        """ML 분석을 위한 요청 데이터 생성"""
        news_data = [
            {
                "title": item.title,
                "description": item.description,
                "link": item.link,
                "pub_date": item.pub_date,
                "mention_count": item.mention_count
            }
            for item in news_response.items
        ]
        
        return NewsAnalysisRequest(news_items=news_data) 