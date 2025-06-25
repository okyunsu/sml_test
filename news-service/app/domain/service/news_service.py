import re
import html
import httpx
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
from contextlib import asynccontextmanager
from app.config.settings import settings
from app.domain.model.news_dto import (
    NewsSearchRequest, NewsSearchResponse, NewsItem, 
    TrendingKeywordsResponse, NewsAnalysisRequest
)

class NewsServiceError(Exception):
    """뉴스 서비스 도메인 예외"""
    pass

class NewsAPIError(NewsServiceError):
    """뉴스 API 관련 예외"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class NewsService:
    """뉴스 검색 서비스 - 비동기 최적화된 비즈니스 로직"""
    
    def __init__(self):
        self.naver_search_url = settings.naver_search_url
        self.client_id = settings.naver_client_id
        self.client_secret = settings.naver_client_secret
        
        # HTTP 클라이언트 설정 (연결 풀 최적화)
        self._http_limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
        
        # 타임아웃 설정
        self._timeout = httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=10.0,
            pool=5.0
        )
        
        if not self.client_id or not self.client_secret:
            raise NewsServiceError("네이버 API 클라이언트 ID와 시크릿이 설정되지 않았습니다.")
    
    @asynccontextmanager
    async def _get_http_client(self):
        """비동기 HTTP 클라이언트 컨텍스트 매니저"""
        async with httpx.AsyncClient(
            limits=self._http_limits,
            timeout=self._timeout,
            headers={"User-Agent": "News-Service/1.0"}
        ) as client:
            yield client
    
    async def search_news(self, search_request: NewsSearchRequest) -> NewsSearchResponse:
        """뉴스 검색 실행 - 비동기 최적화"""
        try:
            # 네이버 API 호출
            response_data = await self._call_naver_api(search_request)
            
            # 응답 데이터 병렬 처리
            raw_items = response_data.get("items", [])
            if not raw_items:
                return self._create_empty_response(search_request, response_data)
            
            # 데이터 정제를 비동기로 처리
            cleaned_items = await self._clean_news_items_async(raw_items)
            original_count = len(cleaned_items)
            
            # 중복 제거 처리
            if search_request.remove_duplicates:
                deduplicated_items = await self._remove_duplicates_async(
                    cleaned_items, 
                    search_request.similarity_threshold
                )
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
            
        except httpx.HTTPStatusError as e:
            raise NewsAPIError(
                self._get_api_error_message(e.response.status_code),
                e.response.status_code
            )
        except httpx.RequestError as e:
            raise NewsAPIError(f"네트워크 오류가 발생했습니다: {str(e)}")
        except Exception as e:
            raise NewsServiceError(f"뉴스 검색 중 오류가 발생했습니다: {str(e)}")
    
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
    
    async def _clean_news_items_async(self, raw_items: List[Dict[str, Any]]) -> List[NewsItem]:
        """뉴스 아이템들을 비동기로 정제"""
        # CPU 집약적 작업을 위한 배치 처리
        batch_size = 50
        tasks = []
        
        for i in range(0, len(raw_items), batch_size):
            batch = raw_items[i:i + batch_size]
            task = asyncio.create_task(self._process_news_batch(batch))
            tasks.append(task)
        
        # 모든 배치를 병렬로 처리
        batch_results = await asyncio.gather(*tasks)
        
        # 결과 병합
        cleaned_items = []
        for batch_result in batch_results:
            cleaned_items.extend(batch_result)
        
        return cleaned_items
    
    async def _process_news_batch(self, batch: List[Dict[str, Any]]) -> List[NewsItem]:
        """뉴스 배치를 처리"""
        # I/O 블로킹을 방지하기 위해 작은 지연 추가
        await asyncio.sleep(0)
        return [self._clean_news_item(item) for item in batch]
    
    async def _remove_duplicates_async(self, news_items: List[NewsItem], similarity_threshold: float = 0.75) -> List[NewsItem]:
        """비동기 중복 제거"""
        if not news_items:
            return []
        
        # 중복 제거는 CPU 집약적이므로 배치로 처리
        if len(news_items) > 100:
            return await self._remove_duplicates_large_dataset(news_items, similarity_threshold)
        else:
            return await self._remove_duplicates_small_dataset(news_items, similarity_threshold)
    
    async def _remove_duplicates_small_dataset(self, news_items: List[NewsItem], similarity_threshold: float) -> List[NewsItem]:
        """소규모 데이터셋 중복 제거"""
        await asyncio.sleep(0)  # 다른 코루틴에게 제어권 양보
        return self._remove_duplicates_sync(news_items, similarity_threshold)
    
    async def _remove_duplicates_large_dataset(self, news_items: List[NewsItem], similarity_threshold: float) -> List[NewsItem]:
        """대규모 데이터셋 중복 제거 (병렬 처리)"""
        chunk_size = 50
        chunks = [news_items[i:i + chunk_size] for i in range(0, len(news_items), chunk_size)]
        
        # 각 청크를 병렬로 처리
        tasks = []
        for chunk in chunks:
            task = asyncio.create_task(self._process_duplicate_chunk(chunk, similarity_threshold))
            tasks.append(task)
        
        chunk_results = await asyncio.gather(*tasks)
        
        # 청크 결과들을 병합하고 최종 중복 제거
        all_items = []
        for chunk_result in chunk_results:
            all_items.extend(chunk_result)
        
        # 청크 간 중복 제거
        return await self._remove_duplicates_small_dataset(all_items, similarity_threshold)
    
    async def _process_duplicate_chunk(self, chunk: List[NewsItem], similarity_threshold: float) -> List[NewsItem]:
        """중복 제거 청크 처리"""
        await asyncio.sleep(0)
        return self._remove_duplicates_sync(chunk, similarity_threshold)
    
    def _remove_duplicates_sync(self, news_items: List[NewsItem], similarity_threshold: float) -> List[NewsItem]:
        """동기 중복 제거 (기존 로직)"""
        unique_news = []
        processed_indices = set()
        
        for i, current_item in enumerate(news_items):
            if i in processed_indices:
                continue
                
            similar_items = [current_item]
            
            for j, compare_item in enumerate(news_items[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                    
                similarity = self._calculate_similarity(current_item, compare_item)
                
                if similarity >= similarity_threshold:
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
    
    def _get_api_error_message(self, status_code: int) -> str:
        """API 에러 코드에 따른 메시지 반환"""
        error_messages = {
            400: "잘못된 요청 파라미터입니다.",
            401: "네이버 API 인증에 실패했습니다.",
            429: "API 호출 한도를 초과했습니다.",
        }
        return error_messages.get(status_code, f"네이버 API 호출 중 오류가 발생했습니다: {status_code}")
    
    async def get_trending_keywords(self) -> TrendingKeywordsResponse:
        """한국 주요 기업 키워드 조회 - 비동기 최적화"""
        # 실제 환경에서는 데이터베이스나 캐시에서 비동기로 조회
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
    
    def _calculate_similarity(self, item1: NewsItem, item2: NewsItem) -> float:
        """두 뉴스 아이템 간의 유사도 계산"""
        title_similarity = self._text_similarity(
            self._normalize_text(item1.title),
            self._normalize_text(item2.title)
        )
        
        desc_similarity = self._text_similarity(
            self._normalize_text(item1.description),
            self._normalize_text(item2.description)
        )
        
        return (title_similarity * 0.7) + (desc_similarity * 0.3)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도 계산"""
        if not text1 or not text2:
            return 0.0
        
        text1_truncated = text1[:200]
        text2_truncated = text2[:200]
        
        return SequenceMatcher(None, text1_truncated, text2_truncated).ratio()
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        if not text:
            return ""
        
        normalized = re.sub(r'[^\w\s가-힣]', ' ', text)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip().lower()
    
    async def _call_naver_api(self, search_request: NewsSearchRequest) -> Dict[str, Any]:
        """네이버 검색 API 호출 - 연결 풀 최적화"""
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
        
        async with self._get_http_client() as client:
            response = await client.get(
                self.naver_search_url,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    def _clean_news_item(self, item: Dict[str, Any]) -> NewsItem:
        """뉴스 아이템 데이터 정제"""
        return NewsItem(
            title=self._clean_html_text(item.get("title", "")),
            original_link=item.get("originallink", ""),
            link=item.get("link", ""),
            description=self._clean_html_text(item.get("description", "")),
            pub_date=item.get("pubDate", ""),
            mention_count=1,
            similarity_score=None
        )
    
    def _clean_html_text(self, text: str) -> str:
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