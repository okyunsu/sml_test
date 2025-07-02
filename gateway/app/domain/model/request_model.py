from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ✅ 뉴스 검색 요청용 Pydantic 모델
class NewsSearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리", examples=["삼성전자"])
    max_results: Optional[int] = Field(default=100, description="최대 결과 수", examples=[100])
    sort_by: Optional[str] = Field(default="accuracy", description="정렬 기준 (accuracy, date)", examples=["accuracy"])
    category: Optional[str] = Field(default=None, description="카테고리 필터", examples=["technology"])
    date_from: Optional[str] = Field(default=None, description="시작 날짜 (YYYY-MM-DD)", examples=["2024-01-01"])
    date_to: Optional[str] = Field(default=None, description="종료 날짜 (YYYY-MM-DD)", examples=["2024-12-31"])


# ✅ 회사 뉴스 검색 요청용 모델
class CompanyNewsRequest(BaseModel):
    company: str = Field(..., description="회사명", examples=["삼성전자"])
    max_results: Optional[int] = Field(default=100, description="최대 결과 수", examples=[100])
    analysis_type: Optional[str] = Field(default="sentiment", description="분석 타입", examples=["sentiment"])


# ✅ 배치 검색 요청용 모델
class BatchNewsRequest(BaseModel):
    requests: List[NewsSearchRequest] = Field(..., description="배치 검색 요청 목록")


# ✅ 일반적인 요청 모델 (모든 타입의 요청 처리용)
class GenericRequest(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict, description="요청 데이터")
    

# ✅ 기존 Finance 모델 (호환성을 위해 유지)
class FinanceRequest(BaseModel):
    company_name: str = Field(..., description="회사명", examples=["샘플전자"])
    