from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class NewsItem(BaseModel):
    """개별 뉴스 아이템"""
    title: str = Field(..., description="뉴스 제목 (HTML 태그 제거됨)")
    original_link: str = Field(..., description="뉴스 원문 링크")
    link: str = Field(..., description="네이버 뉴스 링크")
    description: str = Field(..., description="뉴스 요약 (HTML 태그 제거됨)")
    pub_date: str = Field(..., description="뉴스 발행일")
    mention_count: Optional[int] = Field(1, description="동일/유사 뉴스 언급 횟수")
    similarity_score: Optional[float] = Field(None, description="대표 뉴스와의 유사도 점수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "ESG 경영 확산으로 지속가능한 성장 기대",
                "original_link": "https://example.com/news/123",
                "link": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=101&oid=001&aid=123",
                "description": "ESG 경영이 기업의 지속가능한 성장을 위한 핵심 전략으로 부상하고 있다...",
                "pub_date": "Mon, 25 Dec 2023 09:00:00 +0900",
                "mention_count": 3,
                "similarity_score": 0.95
            }
        }

class NewsSearchRequest(BaseModel):
    """뉴스 검색 요청"""
    query: str = Field(..., min_length=1, max_length=100, description="검색어")
    display: int = Field(10, ge=1, le=100, description="검색 결과 출력 건수 (1~100)")
    start: int = Field(1, ge=1, le=1000, description="검색 시작 위치 (1~1000)")
    sort: str = Field("sim", pattern="^(sim|date)$", description="정렬 옵션 (sim: 정확도순, date: 날짜순)")
    remove_duplicates: bool = Field(True, description="중복 뉴스 제거 여부")
    similarity_threshold: float = Field(0.75, ge=0.0, le=1.0, description="유사도 임계값 (0.0~1.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "ESG",
                "display": 10,
                "start": 1,
                "sort": "date",
                "remove_duplicates": True,
                "similarity_threshold": 0.8
            }
        }

class SimpleCompanySearchRequest(BaseModel):
    """간소화된 회사별 뉴스 검색 요청 - 회사명만 입력"""
    company: str = Field(..., min_length=1, max_length=50, description="회사명")
    
    def to_optimized_news_search_request(self) -> NewsSearchRequest:
        """최적화된 NewsSearchRequest로 변환"""
        return NewsSearchRequest(
            query=f'"{self.company}"',  # 정확한 검색을 위해 따옴표 사용
            display=100,                # 충분한 뉴스 수집
            start=1,                    # 가장 최신/관련성 높은 뉴스부터
            sort="sim",                 # 정확도 순 정렬 (관련성 높은 뉴스 우선)
            remove_duplicates=True,     # 중복 제거 활성화
            similarity_threshold=0.75   # 적절한 유사도 임계값
        )
    
    class Config:
        json_schema_extra = {
            "example": {
                "company": "삼성전자"
            }
        }

class CompanyNewsRequest(BaseModel):
    """회사별 뉴스 검색 요청 (고급 사용자용)"""
    company: str = Field(..., min_length=1, max_length=50, description="회사명")
    display: int = Field(100, ge=1, le=100, description="검색 결과 출력 건수 (1~100)")
    start: int = Field(1, ge=1, le=1000, description="검색 시작 위치 (1~1000)")
    sort: str = Field("date", pattern="^(sim|date)$", description="정렬 옵션 (sim: 정확도순, date: 날짜순)")
    remove_duplicates: bool = Field(True, description="중복 뉴스 제거 여부")
    similarity_threshold: float = Field(0.75, ge=0.0, le=1.0, description="유사도 임계값 (0.0~1.0)")
    
    def to_news_search_request(self) -> NewsSearchRequest:
        """CompanyNewsRequest를 NewsSearchRequest로 변환"""
        return NewsSearchRequest(
            query=f'"{self.company}"',  # 회사명을 따옴표로 감싸서 정확한 검색
            display=self.display,
            start=self.start,
            sort=self.sort,
            remove_duplicates=self.remove_duplicates,
            similarity_threshold=self.similarity_threshold
        )
    
    class Config:
        json_schema_extra = {
            "example": {
                "company": "삼성전자",
                "display": 100,
                "start": 1,
                "sort": "date",
                "remove_duplicates": True,
                "similarity_threshold": 0.75
            }
        }

class NewsSearchResponse(BaseModel):
    """뉴스 검색 응답"""
    last_build_date: str = Field(..., description="검색 결과를 생성한 시간")
    total: int = Field(..., description="검색 결과 문서의 총 개수")
    start: int = Field(..., description="검색 시작 위치")
    display: int = Field(..., description="한 번에 표시할 검색 결과 개수")
    items: List[NewsItem] = Field(..., description="뉴스 검색 결과")
    original_count: Optional[int] = Field(None, description="중복 제거 전 뉴스 개수")
    duplicates_removed: Optional[int] = Field(None, description="제거된 중복 뉴스 개수")
    deduplication_enabled: Optional[bool] = Field(None, description="중복 제거 활성화 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "last_build_date": "Mon, 25 Dec 2023 10:30:00 +0900",
                "total": 500,
                "start": 1,
                "display": 10,
                "items": [
                    {
                        "title": "ESG 경영 확산으로 지속가능한 성장 기대",
                        "original_link": "https://example.com/news/123",
                        "link": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=101&oid=001&aid=123",
                        "description": "ESG 경영이 기업의 지속가능한 성장을 위한 핵심 전략으로 부상하고 있다...",
                        "pub_date": "Mon, 25 Dec 2023 09:00:00 +0900",
                        "mention_count": 3,
                        "similarity_score": 0.95
                    }
                ],
                "original_count": 15,
                "duplicates_removed": 5,
                "deduplication_enabled": True
            }
        }

# ML 분석 관련 DTO 추가
class ESGClassification(BaseModel):
    """ESG 분류 결과"""
    esg_category: str = Field(..., description="ESG 카테고리")
    confidence_score: float = Field(..., description="신뢰도 점수")
    keywords: List[str] = Field(default_factory=list, description="분류에 사용된 키워드")
    classification_method: str = Field(..., description="분류 방법")

class SentimentAnalysis(BaseModel):
    """감정 분석 결과"""
    sentiment: str = Field(..., description="감정 (긍정/부정/중립)")
    confidence_score: float = Field(..., description="신뢰도 점수")
    positive: float = Field(..., description="긍정 점수")
    negative: float = Field(..., description="부정 점수")
    neutral: float = Field(..., description="중립 점수")
    analysis_method: str = Field(..., description="분석 방법")

class AnalyzedNewsItem(BaseModel):
    """분석된 뉴스 아이템"""
    news_item: NewsItem = Field(..., description="원본 뉴스 아이템")
    esg_classification: ESGClassification = Field(..., description="ESG 분류 결과")
    sentiment_analysis: SentimentAnalysis = Field(..., description="감정 분석 결과")

class AnalysisSummary(BaseModel):
    """분석 요약"""
    total_analyzed: int = Field(..., description="분석된 뉴스 총 개수")
    esg_distribution: Dict[str, int] = Field(..., description="ESG 카테고리별 분포")
    sentiment_distribution: Dict[str, int] = Field(..., description="감정별 분포")

class NewsAnalysisRequest(BaseModel):
    """뉴스 분석 요청 (ML 서비스용)"""
    news_items: List[Dict[str, Any]] = Field(..., description="분석할 뉴스 아이템 목록")

class NewsAnalysisResponse(BaseModel):
    """뉴스 분석 응답"""
    search_info: Dict[str, Any] = Field(..., description="검색 정보")
    analyzed_news: List[AnalyzedNewsItem] = Field(..., description="분석된 뉴스 목록")
    analysis_summary: AnalysisSummary = Field(..., description="분석 요약")
    ml_service_status: str = Field(..., description="ML 서비스 상태")

class TrendingKeywordsResponse(BaseModel):
    """트렌딩 키워드 응답"""
    keywords: List[str] = Field(..., description="키워드 목록")
    category: str = Field(..., description="카테고리")
    last_updated: str = Field(..., description="마지막 업데이트 시간")

class ErrorResponse(BaseModel):
    """에러 응답"""
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "INVALID_REQUEST",
                "error_message": "검색어가 필요합니다.",
                "timestamp": "2023-12-25T10:30:00"
            }
        } 