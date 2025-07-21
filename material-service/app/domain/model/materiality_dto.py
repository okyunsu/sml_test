from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MaterialityTopic(BaseModel):
    """중대성 평가 토픽 모델"""
    topic_name: str = Field(..., description="중대성 평가 토픽명")
    priority: int = Field(..., description="우선순위 (1이 가장 중요)")
    year: int = Field(..., description="평가 연도")
    company_name: str = Field(..., description="기업명")
    sasb_mapping: Optional[str] = Field(None, description="매핑된 SASB 이슈 코드")
    
class MaterialityAssessment(BaseModel):
    """연도별 중대성 평가 전체 결과"""
    assessment_id: str = Field(..., description="평가 ID")
    company_name: str = Field(..., description="기업명")
    year: int = Field(..., description="평가 연도")
    topics: List[MaterialityTopic] = Field(..., description="중대성 평가 토픽 목록")
    upload_date: datetime = Field(default_factory=datetime.now, description="업로드 일시")
    
class MaterialityHistory(BaseModel):
    """기업별 중대성 평가 히스토리"""
    company_name: str = Field(..., description="기업명")
    assessments: List[MaterialityAssessment] = Field(..., description="연도별 평가 결과")
    
    def get_assessment_by_year(self, year: int) -> Optional[MaterialityAssessment]:
        """특정 연도의 평가 결과 조회"""
        for assessment in self.assessments:
            if assessment.year == year:
                return assessment
        return None
    
    def get_years(self) -> List[int]:
        """평가가 이루어진 연도 목록 반환"""
        return sorted([assessment.year for assessment in self.assessments])
    
    def get_topic_trend(self, topic_name: str) -> List[Dict[str, Any]]:
        """특정 토픽의 연도별 우선순위 변화 추이"""
        trend = []
        for assessment in self.assessments:
            for topic in assessment.topics:
                if topic.topic_name == topic_name:
                    trend.append({
                        "year": assessment.year,
                        "priority": topic.priority,
                        "sasb_mapping": topic.sasb_mapping
                    })
        return sorted(trend, key=lambda x: x["year"])

class SASBMaterialityMapping(BaseModel):
    """SASB 이슈와 중대성 평가 토픽 매핑"""
    sasb_code: str = Field(..., description="SASB 이슈 코드")
    sasb_name: str = Field(..., description="SASB 이슈명")
    sasb_category: str = Field(..., description="ESG 카테고리 (E/S/G)")
    materiality_topics: List[str] = Field(..., description="매핑된 중대성 평가 토픽들")
    
class IssueChangeType(str, Enum):
    """이슈 변화 유형"""
    EMERGING = "emerging"      # 부상 이슈
    ONGOING = "ongoing"        # 지속 이슈
    MATURING = "maturing"      # 성숙 이슈
    DECLINING = "declining"    # 감소 이슈
    NEW = "new"               # 신규 이슈

class MaterialityTrendAnalysis(BaseModel):
    """중대성 평가 트렌드 분석 결과"""
    company_name: str = Field(..., description="기업명")
    analysis_period: str = Field(..., description="분석 기간 (예: 2022-2024)")
    
    # 토픽별 변화 분석
    topic_changes: List[Dict[str, Any]] = Field(..., description="토픽별 변화 분석")
    
    # 이슈 분류 결과
    emerging_issues: List[Dict[str, Any]] = Field(..., description="부상 이슈")
    ongoing_issues: List[Dict[str, Any]] = Field(..., description="지속 이슈")
    maturing_issues: List[Dict[str, Any]] = Field(..., description="성숙 이슈")
    
    # 뉴스 빈도 분석
    news_frequency_analysis: Dict[str, Any] = Field(..., description="뉴스 빈도 분석 결과")
    
    # 제안사항
    recommendations: List[Dict[str, Any]] = Field(..., description="차년도 중대성 평가 제안사항")

class MaterialityUpdateRecommendation(BaseModel):
    """중대성 평가 업데이트 제안"""
    topic_name: str = Field(..., description="제안 토픽명")
    change_type: IssueChangeType = Field(..., description="변화 유형")
    rationale: str = Field(..., description="제안 근거")
    related_keywords: List[str] = Field(..., description="관련 키워드")
    news_count: int = Field(..., description="관련 뉴스 건수")
    confidence_score: float = Field(..., description="신뢰도 점수 (0-1)")
    sasb_alignment: str = Field(..., description="SASB 이슈 연관성")
    
class MaterialityComparisonResult(BaseModel):
    """중대성 평가 비교 분석 결과"""
    company_name: str = Field(..., description="기업명")
    base_year: int = Field(..., description="기준 연도")
    comparison_year: int = Field(..., description="비교 연도")
    
    # 순위 변화 분석
    priority_changes: List[Dict[str, Any]] = Field(..., description="우선순위 변화")
    
    # 신규/제거 토픽
    new_topics: List[str] = Field(..., description="신규 추가된 토픽")
    removed_topics: List[str] = Field(..., description="제거된 토픽")
    
    # 안정성 지표
    stability_score: float = Field(..., description="평가 안정성 점수")
    
    # 뉴스 연관성
    news_correlation: Dict[str, Any] = Field(..., description="뉴스와의 연관성 분석")

# 파일 업로드 관련 모델
class FileUploadRequest(BaseModel):
    """파일 업로드 요청"""
    company_name: str = Field(..., description="기업명")
    year: int = Field(..., description="평가 연도")
    file_format: str = Field(default="simple_list", description="파일 형식")

class FileUploadResponse(BaseModel):
    """파일 업로드 응답"""
    success: bool = Field(..., description="성공 여부")
    assessment_id: str = Field(..., description="평가 ID")
    message: str = Field(..., description="응답 메시지")
    validation_result: Optional[Dict[str, Any]] = Field(None, description="검증 결과")

class MaterialityAnalysisRequest(BaseModel):
    """중대성 평가 분석 요청"""
    company_name: str = Field(..., description="기업명")
    base_year: int = Field(..., description="기준 연도")
    comparison_year: int = Field(..., description="비교 연도")
    include_news_analysis: bool = Field(True, description="뉴스 분석 포함 여부")

class MaterialityAnalysisResponse(BaseModel):
    """중대성 평가 분석 응답"""
    analysis_id: str = Field(..., description="분석 ID")
    trend_analysis: MaterialityTrendAnalysis = Field(..., description="트렌드 분석 결과")
    comparison_result: MaterialityComparisonResult = Field(..., description="비교 분석 결과")
    recommendations: List[MaterialityUpdateRecommendation] = Field(..., description="업데이트 제안사항") 