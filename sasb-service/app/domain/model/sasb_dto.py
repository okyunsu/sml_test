from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NewsAnalysisRequest(BaseModel):
    """
    Request model for triggering a news analysis.
    It requires one or more keywords to search for.
    """
    keywords: List[str] = Field(..., description="List of keywords to search for news.", min_length=1)

class NewsItem(BaseModel):
    """
    Represents a single news article retrieved from the search.
    """
    title: str = Field(..., description="The title of the news article.")
    link: str = Field(..., description="The URL link to the original news article.")
    description: str = Field(..., description="A short description or snippet of the news article.")

class SentimentResult(BaseModel):
    """
    Represents the sentiment analysis result for a single news item.
    """
    sentiment: str = Field(..., description="The predicted sentiment (e.g., 'positive', 'negative', 'neutral').")
    confidence: float = Field(..., description="The confidence score of the sentiment prediction.")

class AnalyzedNewsArticle(NewsItem):
    """
    Represents a news article that has been analyzed for sentiment.
    """
    sentiment: SentimentResult

class NewsAnalysisResult(BaseModel):
    """
    The final result of a news analysis task, containing all analyzed articles.
    Enhanced for SASB service with additional fields.
    """
    task_id: str
    status: str
    searched_keywords: List[str]
    total_articles_found: int
    analyzed_articles: Optional[List[AnalyzedNewsArticle]] = None
    error_message: Optional[str] = None
    company_name: Optional[str] = None  # 분석 대상 회사명
    analysis_type: Optional[str] = None  # "company_sasb" 또는 "sasb_only"
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

class SASBAnalysisRequest(BaseModel):
    """
    SASB 분석 요청 모델 - 두 가지 분석 타입 지원
    """
    company_name: Optional[str] = Field(None, description="분석할 회사명 (SASB 전용 분석 시 None)")
    sasb_keywords: Optional[List[str]] = Field(None, description="SASB 키워드 목록 (미지정시 기본값 사용)")
    max_results: int = Field(10, description="수집할 최대 뉴스 개수")
    analysis_type: str = Field(..., description="분석 타입: 'company_sasb' 또는 'sasb_only'")

class SASBKeywordInfo(BaseModel):
    """
    SASB 키워드 정보 모델
    """
    keyword: str = Field(..., description="SASB 키워드")
    category: str = Field(..., description="ESG 카테고리 (E/S/G)")
    description: str = Field(..., description="키워드 설명")
    
class SASBAnalysisStats(BaseModel):
    """
    SASB 분석 통계 모델
    """
    total_companies: int = Field(..., description="모니터링 중인 회사 수")
    total_keywords: int = Field(..., description="사용 중인 SASB 키워드 수")
    cache_hit_rate: float = Field(..., description="캐시 히트율")
    last_analysis: Optional[str] = Field(None, description="마지막 분석 시각") 