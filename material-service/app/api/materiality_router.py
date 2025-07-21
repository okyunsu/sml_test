from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..domain.service.materiality_file_service import MaterialityFileService
from ..domain.model.materiality_dto import MaterialityAssessment

logger = logging.getLogger(__name__)

# 메인 라우터
materiality_router = APIRouter(prefix="/api/v1/materiality", tags=["중대성 평가 관리"])

# =============================================================================
# 📊 기본 관리 엔드포인트
# =============================================================================

@materiality_router.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "material-assessment-service",
        "version": "2.0.0"
    }

@materiality_router.get("/companies")
async def get_supported_companies():
    """지원 기업 목록 조회"""
    try:
        file_service = MaterialityFileService()
        supported_companies = file_service.get_supported_companies()
        
        company_info = []
        for company in supported_companies:
            file_info = file_service.get_file_info(company)
            company_info.append({
                "company_name": company,
                "has_assessment": bool(file_info),
                "available_years": [2024] if file_info else []
            })
        
        return {
            "status": "success",
            "total_companies": len(supported_companies),
            "companies": company_info
        }
        
    except Exception as e:
        logger.error(f"지원 기업 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"지원 기업 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@materiality_router.get("/companies/{company_name}/assessment/{year}")
async def get_company_assessment(company_name: str, year: int):
    """특정 회사의 특정 연도 중대성 평가 조회"""
    try:
        file_service = MaterialityFileService()
        
        # 지원 기업 확인
        supported_companies = file_service.get_supported_companies()
        if company_name not in supported_companies:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 기업입니다. 지원 기업: {', '.join(supported_companies)}"
            )
        
        # 중대성 평가 데이터 로드
        assessment = file_service.load_company_assessment(company_name, year)
        if not assessment:
            raise HTTPException(
                status_code=404,
                detail=f"'{company_name}' 기업의 {year}년 중대성 평가 데이터를 찾을 수 없습니다."
            )
        
        return assessment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"중대성 평가 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"중대성 평가 조회 중 오류가 발생했습니다: {str(e)}"
        )

# =============================================================================
# 🏢 회사별 중대성 분석 엔드포인트
# =============================================================================

@materiality_router.post("/companies/{company_name}/analyze")
async def analyze_company_materiality(
    company_name: str,
    year: int = Query(default=2024, description="분석 연도"),
    include_news: bool = Query(default=True, description="뉴스 분석 포함 여부"),
    max_articles: int = Query(default=100, description="분석할 최대 뉴스 수")
):
    """💼 회사별 중대성 평가 분석
    
    뉴스 데이터를 활용한 회사별 중대성 평가 분석을 수행합니다.
    - 기존 중대성 평가 대비 변화 분석
    - 뉴스 기반 이슈 영향도 분석
    - 중대성 평가 업데이트 제안
    
    ⚠️ 주의: 뉴스 분석 결과는 참고용이며, 실제 중대성 평가는 다양한 이해관계자 의견을 종합하여 수행해야 합니다.
    """
    try:
        from ..domain.service.materiality_analysis_service import MaterialityAnalysisService
        
        file_service = MaterialityFileService()
        analysis_service = MaterialityAnalysisService()
        
        # 지원 기업 확인
        supported_companies = file_service.get_supported_companies()
        if company_name not in supported_companies:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 기업입니다. 지원 기업: {', '.join(supported_companies)}"
            )
        
        # 기준 평가 로드
        base_assessment = file_service.load_company_assessment(company_name, year - 1)
        
        # 중대성 평가 분석 수행
        analysis_result = await analysis_service.analyze_materiality_changes(
            company_name=company_name,
            current_year=year,
            base_assessment=base_assessment,
            include_news=include_news,
            max_articles=max_articles
        )
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회사별 중대성 분석 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"회사별 중대성 분석 중 오류가 발생했습니다: {str(e)}"
        )

@materiality_router.get("/companies/{company_name}/compare")
async def compare_company_assessments(
    company_name: str,
    year1: int = Query(description="비교 기준 연도"),
    year2: int = Query(description="비교 대상 연도")
):
    """🔄 회사별 중대성 평가 비교 분석
    
    두 연도의 중대성 평가를 비교 분석합니다.
    - 토픽별 우선순위 변화
    - 신규/제거된 토픽 식별
    - 변화 패턴 분석
    """
    try:
        file_service = MaterialityFileService()
        
        # 지원 기업 확인
        supported_companies = file_service.get_supported_companies()
        if company_name not in supported_companies:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 기업입니다. 지원 기업: {', '.join(supported_companies)}"
            )
        
        # 두 연도 평가 로드
        assessment1 = file_service.load_company_assessment(company_name, year1)
        assessment2 = file_service.load_company_assessment(company_name, year2)
        
        if not assessment1:
            raise HTTPException(
                status_code=404,
                detail=f"'{company_name}' 기업의 {year1}년 중대성 평가 데이터를 찾을 수 없습니다."
            )
        
        if not assessment2:
            raise HTTPException(
                status_code=404,
                detail=f"'{company_name}' 기업의 {year2}년 중대성 평가 데이터를 찾을 수 없습니다."
            )
        
        # 비교 분석 수행
        topics1 = {topic.topic_name: topic.priority for topic in assessment1.topics}
        topics2 = {topic.topic_name: topic.priority for topic in assessment2.topics}
        
        # 변화 분석
        priority_changes = []
        for topic_name in topics1:
            if topic_name in topics2:
                change = topics1[topic_name] - topics2[topic_name]
                if change != 0:
                    priority_changes.append({
                        "topic_name": topic_name,
                        "previous_priority": topics1[topic_name],
                        "current_priority": topics2[topic_name],
                        "change": change,
                        "change_type": "improved" if change > 0 else "declined"
                    })
        
        # 신규/제거된 토픽
        new_topics = [name for name in topics2 if name not in topics1]
        removed_topics = [name for name in topics1 if name not in topics2]
        
        return {
            "status": "success",
            "company_name": company_name,
            "comparison_period": f"{year1} vs {year2}",
            "analysis_date": datetime.now().isoformat(),
            "comparison_summary": {
                "total_topics_year1": len(assessment1.topics),
                "total_topics_year2": len(assessment2.topics),
                "priority_changes": len(priority_changes),
                "new_topics": len(new_topics),
                "removed_topics": len(removed_topics)
            },
            "detailed_comparison": {
                "priority_changes": priority_changes,
                "new_topics": new_topics,
                "removed_topics": removed_topics
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"중대성 평가 비교 분석 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"중대성 평가 비교 분석 중 오류가 발생했습니다: {str(e)}"
        )

# =============================================================================
# 🏭 산업별 중대성 이슈 분석 엔드포인트
# =============================================================================

@materiality_router.post("/industries/{industry}/analyze")
async def analyze_industry_materiality(
    industry: str,
    year: int = Query(default=2024, description="분석 연도"),
    max_articles: int = Query(default=200, description="분석할 최대 뉴스 수"),
    include_sasb_mapping: bool = Query(default=True, description="SASB 매핑 포함 여부")
):
    """🏭 산업별 중대성 이슈 분석
    
    특정 산업에서 중요한 중대성 이슈들을 분석합니다.
    - 산업 관련 뉴스 데이터 수집 및 분석
    - 산업별 주요 SASB 이슈 식별
    - 이슈별 중요도 및 트렌드 분석
    
    지원 산업: 금융업, 제조업, 건설업, 에너지업, IT업, 유통업 등
    
    ⚠️ 주의: 산업 분석 결과는 참고용이며, 실제 중대성 평가는 기업별 특성을 고려하여 수행해야 합니다.
    """
    try:
        from ..domain.service.industry_analysis_service import IndustryAnalysisService
        
        # 산업 분석 서비스 초기화
        industry_service = IndustryAnalysisService()
        
        # 지원 산업 확인
        supported_industries = industry_service.get_supported_industries()
        if industry not in supported_industries:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 산업입니다. 지원 산업: {', '.join(supported_industries)}"
            )
        
        # 산업별 중대성 이슈 분석 수행
        analysis_result = await industry_service.analyze_industry_materiality(
            industry=industry,
            year=year,
            max_articles=max_articles,
            include_sasb_mapping=include_sasb_mapping
        )
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"산업별 중대성 분석 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"산업별 중대성 분석 중 오류가 발생했습니다: {str(e)}"
        )

@materiality_router.get("/industries")
async def get_supported_industries():
    """지원 산업 목록 조회"""
    try:
        from ..domain.service.industry_analysis_service import IndustryAnalysisService
        
        industry_service = IndustryAnalysisService()
        supported_industries = industry_service.get_supported_industries()
        
        # 산업별 정보 제공
        industry_info = []
        for industry in supported_industries:
            info = industry_service.get_industry_info(industry)
            industry_info.append({
                "industry_name": industry,
                "description": info.get("description", ""),
                "key_sasb_topics": info.get("key_sasb_topics", []),
                "related_companies": info.get("related_companies", [])
            })
        
        return {
            "status": "success",
            "total_industries": len(supported_industries),
            "industries": industry_info
        }
        
    except Exception as e:
        logger.error(f"지원 산업 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"지원 산업 목록 조회 중 오류가 발생했습니다: {str(e)}"
        ) 