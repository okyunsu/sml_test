import asyncio
from typing import List, Optional
from fastapi import HTTPException, status

from app.domain.model.sasb_dto import NewsAnalysisResult, AnalyzedNewsArticle
from app.domain.service.analysis_service import AnalysisService
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class SASBController:
    """SASB 컨트롤러 - 비즈니스 로직과 API 분리"""
    
    def __init__(self):
        self.analysis_service = AnalysisService()
    
    async def analyze_company_sasb_news(
        self, 
        company_name: str, 
        sasb_keywords: Optional[List[str]] = None,
        max_results: int = 100
    ) -> NewsAnalysisResult:
        """회사 + SASB 키워드 조합 뉴스 분석"""
        try:
            # 기본 SASB 키워드 사용 (미지정 시)
            if not sasb_keywords:
                sasb_keywords = self._get_default_sasb_keywords()
            
            # 분석 실행
            analyzed_articles = await self.analysis_service.analyze_and_cache_news(
                keywords=sasb_keywords,
                company_name=company_name
            )
            
            # 결과 제한
            if len(analyzed_articles) > max_results:
                analyzed_articles = analyzed_articles[:max_results]
            
            return NewsAnalysisResult(
                task_id=f"company_sasb_{company_name}_{hash(str(sasb_keywords))}",
                status="completed",
                searched_keywords=sasb_keywords,
                total_articles_found=len(analyzed_articles),
                analyzed_articles=analyzed_articles,
                company_name=company_name,
                analysis_type="company_sasb"
            )
            
        except Exception as e:
            logger.error(f"회사+SASB 분석 실패 ({company_name}): {str(e)}")
            return NewsAnalysisResult(
                task_id=f"company_sasb_{company_name}_error",
                status="error",
                searched_keywords=sasb_keywords or [],
                total_articles_found=0,
                analyzed_articles=[],
                error_message=str(e),
                company_name=company_name,
                analysis_type="company_sasb"
            )
    
    async def analyze_sasb_only_news(
        self, 
        sasb_keywords: Optional[List[str]] = None,
        max_results: int = 20
    ) -> NewsAnalysisResult:
        """SASB 키워드 전용 뉴스 분석 (회사명 없음)"""
        try:
            # 기본 SASB 키워드 사용 (미지정 시)
            if not sasb_keywords:
                sasb_keywords = self._get_default_sasb_keywords()
            
            # 분석 실행 (회사명 없이)
            analyzed_articles = await self.analysis_service.analyze_and_cache_news(
                keywords=sasb_keywords,
                company_name=None  # 회사명 없음
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
                analysis_type="sasb_only"
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
    
    async def get_analysis_status(self, task_id: str) -> dict:
        """분석 작업 상태 조회"""
        try:
            # Redis에서 작업 상태 조회 로직
            # 현재는 간단한 응답 반환
            return {
                "task_id": task_id,
                "status": "completed",
                "message": "분석이 완료되었습니다."
            }
        except Exception as e:
            logger.error(f"작업 상태 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"작업 상태 조회 중 오류: {str(e)}"
            )
    
    def _get_default_sasb_keywords(self) -> List[str]:
        """기본 SASB 키워드 목록 반환"""
        return [
            "Scope 1 배출", "Scope 2 배출", "Scope 3 배출",
            "재생에너지 사용 비율", "탄소 저감 목표", "환경 리스크 공시",
            "기후변화 관련 재무 리스크", "ESG 투자", "지속가능채권",
            "녹색채권", "탄소배출권", "RE100", "공급망 투명성", "환경규제 대응"
        ]
    
    def _validate_inputs(self, company_name: Optional[str], sasb_keywords: List[str]) -> None:
        """입력값 검증"""
        if not sasb_keywords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SASB 키워드가 제공되지 않았습니다."
            )
        
        if company_name and len(company_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="회사명이 비어있습니다."
            ) 