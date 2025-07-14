from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .analysis_service import AnalysisService
from .naver_news_service import NaverNewsService
from .ml_inference_service import MLInferenceService
from ..model.sasb_dto import NewsAnalysisResult, AnalyzedNewsArticle, SASBKeywordInfo, SASBAnalysisStats

logger = logging.getLogger(__name__)

class SASBService:
    """
    SASB 고수준 비즈니스 서비스
    SASB 프레임워크 기반의 ESG 분석 로직을 제공합니다.
    """
    
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.naver_news_service = NaverNewsService()
        self.ml_inference_service = MLInferenceService()
        
        # SASB 키워드 정보
        self.sasb_keywords_info = self._initialize_sasb_keywords()
    
    def _initialize_sasb_keywords(self) -> List[SASBKeywordInfo]:
        """신재생에너지 산업 특화 SASB 키워드 정보 초기화"""
        return [
            # 1. Greenhouse Gas Emissions & Energy Resource Planning
            SASBKeywordInfo(keyword="탄소중립", category="E", description="온실가스 배출 및 에너지 포트폴리오 계획"),
            SASBKeywordInfo(keyword="탄소배출", category="E", description="온실가스 배출 및 에너지 포트폴리오 계획"),
            SASBKeywordInfo(keyword="온실가스", category="E", description="온실가스 배출 및 에너지 포트폴리오 계획"),
            SASBKeywordInfo(keyword="RE100", category="E", description="온실가스 배출 및 에너지 포트폴리오 계획"),
            SASBKeywordInfo(keyword="CF100", category="E", description="온실가스 배출 및 에너지 포트폴리오 계획"),
            SASBKeywordInfo(keyword="에너지믹스", category="E", description="온실가스 배출 및 에너지 포트폴리오 계획"),
            SASBKeywordInfo(keyword="전원구성", category="E", description="온실가스 배출 및 에너지 포트폴리오 계획"),
            
            # 2. Air Quality
            SASBKeywordInfo(keyword="미세먼지", category="E", description="발전소 운영에서의 대기 오염 물질 배출"),
            SASBKeywordInfo(keyword="대기오염", category="E", description="발전소 운영에서의 대기 오염 물질 배출"),
            SASBKeywordInfo(keyword="황산화물", category="E", description="발전소 운영에서의 대기 오염 물질 배출"),
            SASBKeywordInfo(keyword="질소산화물", category="E", description="발전소 운영에서의 대기 오염 물질 배출"),
            
            # 3. Water Management
            SASBKeywordInfo(keyword="수처리", category="E", description="발전 과정에서의 물 사용 및 수질 영향"),
            SASBKeywordInfo(keyword="폐수", category="E", description="발전 과정에서의 물 사용 및 수질 영향"),
            SASBKeywordInfo(keyword="그린수소", category="E", description="발전 과정에서의 물 사용 및 수질 영향"),
            SASBKeywordInfo(keyword="수전해", category="E", description="발전 과정에서의 물 사용 및 수질 영향"),
            
            # 4. Waste & Byproduct Management
            SASBKeywordInfo(keyword="폐배터리", category="E", description="신재생에너지 설비의 폐기물 처리"),
            SASBKeywordInfo(keyword="폐패널", category="E", description="신재생에너지 설비의 폐기물 처리"),
            SASBKeywordInfo(keyword="폐블레이드", category="E", description="신재생에너지 설비의 폐기물 처리"),
            SASBKeywordInfo(keyword="자원순환", category="E", description="신재생에너지 설비의 폐기물 처리"),
            SASBKeywordInfo(keyword="재활용", category="E", description="신재생에너지 설비의 폐기물 처리"),
            
            # 5. Energy Affordability
            SASBKeywordInfo(keyword="전기요금", category="S", description="전기요금 및 안정적 에너지 공급"),
            SASBKeywordInfo(keyword="에너지복지", category="S", description="전기요금 및 안정적 에너지 공급"),
            SASBKeywordInfo(keyword="SMP", category="S", description="전기요금 및 안정적 에너지 공급"),
            SASBKeywordInfo(keyword="REC", category="S", description="전기요금 및 안정적 에너지 공급"),
            SASBKeywordInfo(keyword="PPA", category="S", description="전기요금 및 안정적 에너지 공급"),
            
            # 6. Workforce Health & Safety
            SASBKeywordInfo(keyword="중대재해", category="S", description="발전소 건설·운영의 작업장 안전"),
            SASBKeywordInfo(keyword="산업재해", category="S", description="발전소 건설·운영의 작업장 안전"),
            SASBKeywordInfo(keyword="감전사고", category="S", description="발전소 건설·운영의 작업장 안전"),
            SASBKeywordInfo(keyword="추락사고", category="S", description="발전소 건설·운영의 작업장 안전"),
            SASBKeywordInfo(keyword="안전보건", category="S", description="발전소 건설·운영의 작업장 안전"),
            
            # 7. End-Use Efficiency & Demand
            SASBKeywordInfo(keyword="에너지효율", category="E", description="에너지 효율과 수요 반응"),
            SASBKeywordInfo(keyword="수요관리", category="E", description="에너지 효율과 수요 반응"),
            SASBKeywordInfo(keyword="가상발전소", category="E", description="에너지 효율과 수요 반응"),
            SASBKeywordInfo(keyword="VPP", category="E", description="에너지 효율과 수요 반응"),
            SASBKeywordInfo(keyword="스마트그리드", category="E", description="에너지 효율과 수요 반응"),
            
            # 8. Critical Incident Management
            SASBKeywordInfo(keyword="ESS화재", category="G", description="치명적 사고 및 비상 상황 대응"),
            SASBKeywordInfo(keyword="폭발", category="G", description="치명적 사고 및 비상 상황 대응"),
            SASBKeywordInfo(keyword="대규모정전", category="G", description="치명적 사고 및 비상 상황 대응"),
            SASBKeywordInfo(keyword="블랙아웃", category="G", description="치명적 사고 및 비상 상황 대응"),
            SASBKeywordInfo(keyword="안전진단", category="G", description="치명적 사고 및 비상 상황 대응"),
            
            # 9. Grid Resiliency
            SASBKeywordInfo(keyword="전력망", category="E", description="전력망의 안정성 및 복원력"),
            SASBKeywordInfo(keyword="계통안정", category="E", description="전력망의 안정성 및 복원력"),
            SASBKeywordInfo(keyword="출력제어", category="E", description="전력망의 안정성 및 복원력"),
            SASBKeywordInfo(keyword="간헐성", category="E", description="전력망의 안정성 및 복원력"),
            SASBKeywordInfo(keyword="송배전망", category="E", description="전력망의 안정성 및 복원력"),
            
            # 10. Ecological Impacts & Community Relations
            SASBKeywordInfo(keyword="입지갈등", category="S", description="생태계와 지역사회 영향"),
            SASBKeywordInfo(keyword="주민수용성", category="S", description="생태계와 지역사회 영향"),
            SASBKeywordInfo(keyword="환경영향평가", category="E", description="생태계와 지역사회 영향"),
            SASBKeywordInfo(keyword="산림훼손", category="E", description="생태계와 지역사회 영향"),
            SASBKeywordInfo(keyword="조류충돌", category="E", description="생태계와 지역사회 영향"),
            SASBKeywordInfo(keyword="이익공유제", category="S", description="생태계와 지역사회 영향")
        ]
    
    async def get_sasb_keywords_info(self) -> List[SASBKeywordInfo]:
        """SASB 키워드 정보 조회"""
        return self.sasb_keywords_info
    
    def get_default_sasb_keywords(self) -> List[str]:
        """기본 SASB 키워드 목록 반환"""
        return [info.keyword for info in self.sasb_keywords_info]
    
    async def analyze_company_with_sasb(
        self, 
        company_name: str, 
        sasb_keywords: Optional[List[str]] = None,
        max_results: int = 10
    ) -> NewsAnalysisResult:
        """회사 + SASB 키워드 조합 분석"""
        try:
            # 기본 키워드 사용 (미지정 시)
            if not sasb_keywords:
                sasb_keywords = self.get_default_sasb_keywords()
            
            # 분석 실행
            analyzed_articles = await self.analysis_service.analyze_and_cache_news(
                keywords=sasb_keywords,
                company_name=company_name
            )
            
            # 결과 제한
            if len(analyzed_articles) > max_results:
                analyzed_articles = analyzed_articles[:max_results]
            
            return NewsAnalysisResult(
                task_id=f"sasb_company_{company_name}_{hash(str(sasb_keywords))}",
                status="completed",
                searched_keywords=sasb_keywords,
                total_articles_found=len(analyzed_articles),
                analyzed_articles=analyzed_articles,
                company_name=company_name,
                analysis_type="company_sasb",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"회사+SASB 분석 실패 ({company_name}): {str(e)}")
            return NewsAnalysisResult(
                task_id=f"sasb_company_{company_name}_error",
                status="error",
                searched_keywords=sasb_keywords or [],
                total_articles_found=0,
                analyzed_articles=[],
                error_message=str(e),
                company_name=company_name,
                analysis_type="company_sasb"
            )
    
    async def analyze_sasb_only(
        self, 
        sasb_keywords: Optional[List[str]] = None,
        max_results: int = 20
    ) -> NewsAnalysisResult:
        """SASB 키워드 전용 분석 (회사명 없음)"""
        try:
            # 기본 키워드 사용 (미지정 시)
            if not sasb_keywords:
                sasb_keywords = self.get_default_sasb_keywords()
            
            # 분석 실행 (회사명 없이)
            analyzed_articles = await self.analysis_service.analyze_and_cache_news(
                keywords=sasb_keywords,
                company_name=None
            )
            
            # 결과 제한
            if len(analyzed_articles) > max_results:
                analyzed_articles = analyzed_articles[:max_results]
            
            return NewsAnalysisResult(
                task_id=f"sasb_only_{hash(str(sasb_keywords))}",
                status="completed",
                searched_keywords=sasb_keywords,
                total_articles_found=len(analyzed_articles),
                analyzed_articles=analyzed_articles,
                company_name=None,
                analysis_type="sasb_only",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"SASB 전용 분석 실패: {str(e)}")
            return NewsAnalysisResult(
                task_id=f"sasb_only_error",
                status="error",
                searched_keywords=sasb_keywords or [],
                total_articles_found=0,
                analyzed_articles=[],
                error_message=str(e),
                company_name=None,
                analysis_type="sasb_only"
            )
    
    async def get_sasb_analysis_stats(self) -> SASBAnalysisStats:
        """SASB 분석 통계 조회"""
        try:
            return SASBAnalysisStats(
                total_companies=2,  # 두산퓨얼셀, LS ELECTRIC
                total_keywords=len(self.sasb_keywords_info),
                cache_hit_rate=0.85,  # 예상 캐시 히트율
                last_analysis=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"SASB 통계 조회 실패: {str(e)}")
            return SASBAnalysisStats(
                total_companies=0,
                total_keywords=0,
                cache_hit_rate=0.0,
                last_analysis=None
            )
    
    def categorize_keywords_by_esg(self, keywords: List[str]) -> Dict[str, List[str]]:
        """키워드를 ESG 카테고리별로 분류"""
        categorized = {"E": [], "S": [], "G": []}
        
        keyword_map = {info.keyword: info.category for info in self.sasb_keywords_info}
        
        for keyword in keywords:
            category = keyword_map.get(keyword, "G")  # 기본값은 G(Governance)
            categorized[category].append(keyword)
        
        return categorized 