"""통합 API 라우터 - 캐시 우선 스마트 검색 + 대시보드 + 시스템 관리"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Path
from datetime import datetime

from app.domain.controller.news_controller import NewsController
from app.domain.controller.dashboard_controller import DashboardController
from app.domain.model.news_dto import (
    NewsSearchRequest, NewsSearchResponse, ErrorResponse, CompanyNewsRequest,
    TrendingKeywordsResponse, NewsAnalysisResponse, SimpleCompanySearchRequest
)
from app.core.dependencies import get_dependency, DependencyContainer
import logging

logger = logging.getLogger(__name__)

# 각 기능별 라우터 생성
search_router = APIRouter(prefix="/search", tags=["🔍 Smart Search"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["📊 Dashboard"])
system_router = APIRouter(prefix="/system", tags=["🛠️ System"])

# 의존성 주입 함수들
def get_news_controller(
    container: DependencyContainer = Depends(get_dependency)
) -> NewsController:
    """NewsController 의존성 주입"""
    return container.get("news_controller")

def get_dashboard_controller(
    container: DependencyContainer = Depends(get_dependency)
) -> DashboardController:
    """DashboardController 의존성 주입"""
    return container.get("dashboard_controller")

# ============================================================================
# 🔍 SMART SEARCH ROUTER (캐시 우선 → 실시간)
# ============================================================================

@search_router.post(
    "/news",
    response_model=NewsSearchResponse,
    summary="일반 뉴스 스마트 검색",
    description="""
    **스마트 검색 전략:**
    1. 🚀 캐시 확인 (Redis) → 있으면 즉시 반환 (100ms)
    2. 🔍 캐시 없음 → 실시간 검색 → 캐시 저장 → 반환 (2-5초)
    
    **캐시 유효시간:** 30분
    """
)
async def smart_search_news(
    request: NewsSearchRequest,
    background_tasks: BackgroundTasks,
    news_controller: NewsController = Depends(get_news_controller),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """스마트 뉴스 검색 - 캐시 우선, 실시간 폴백"""
    try:
        # 1단계: 캐시 확인
        cache_key = f"news_search:{hash(request.query + str(request.dict()))}"
        cached_result = await dashboard_controller.get_cache_data(cache_key)
        
        if cached_result:
            logger.info(f"캐시 히트: {request.query}")
            return NewsSearchResponse(**cached_result)
        
        # 2단계: 실시간 검색
        logger.info(f"캐시 미스, 실시간 검색: {request.query}")
        result = await news_controller.search_news(request)
        
        # 3단계: 캐시 저장 (백그라운드)
        background_tasks.add_task(
            dashboard_controller.set_cache_data,
            cache_key, 
            result.dict(),
            expire_minutes=30
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Smart news search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 검색 중 오류: {str(e)}")

@search_router.post(
    "/companies/{company}",
    response_model=NewsSearchResponse,
    summary="회사 뉴스 스마트 검색",
    description="""
    **스마트 검색 전략:**
    1. 🚀 캐시 확인 (Redis) → 있으면 즉시 반환
    2. 🔍 캐시 없음 → 실시간 검색 → 캐시 저장
    
    **최적화된 기본 설정:**
    - 검색 결과: 100개
    - 정렬: 정확도 순
    - 중복 제거: 활성화
    """
)
async def smart_search_company_news(
    background_tasks: BackgroundTasks,
    company: str = Path(..., description="회사명"),
    news_controller: NewsController = Depends(get_news_controller),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 뉴스 스마트 검색 - 캐시 우선, 실시간 폴백"""
    try:
        # 1단계: 캐시 확인
        cache_key = f"company_news:{company}"
        cached_result = await dashboard_controller.get_cache_data(cache_key)
        
        if cached_result:
            logger.info(f"캐시 히트 - 회사: {company}")
            return NewsSearchResponse(**cached_result)
        
        # 2단계: 실시간 검색
        logger.info(f"캐시 미스, 실시간 검색 - 회사: {company}")
        request = SimpleCompanySearchRequest(company=company)
        optimized_request = request.to_optimized_news_search_request()
        result = await news_controller.search_news(optimized_request)
        
        # 3단계: 캐시 저장
        background_tasks.add_task(
            dashboard_controller.set_cache_data,
            cache_key,
            result.dict(),
            expire_minutes=30
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Smart company search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 뉴스 검색 중 오류: {str(e)}")

@search_router.post(
    "/companies/{company}/analyze",
    response_model=NewsAnalysisResponse,
    summary="회사 뉴스 스마트 분석",
    description="""
    **스마트 분석 전략:**
    1. 🚀 분석 결과 캐시 확인 → 있으면 즉시 반환
    2. 🔍 캐시 없음 → 실시간 분석 → 캐시 저장
    
    **분석 내용:**
    - ESG 카테고리 분류
    - 감정 분석 (긍정/부정/중립)
    - 키워드 추출
    """
)
async def smart_analyze_company_news(
    background_tasks: BackgroundTasks,
    company: str = Path(..., description="회사명"),
    news_controller: NewsController = Depends(get_news_controller),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 뉴스 스마트 분석 - 캐시 우선, 실시간 폴백"""
    try:
        # 1단계: 분석 결과 캐시 확인
        cache_key = f"company_analysis:{company}"
        cached_result = await dashboard_controller.get_cache_data(cache_key)
        
        if cached_result:
            logger.info(f"분석 캐시 히트 - 회사: {company}")
            return NewsAnalysisResponse(**cached_result)
        
        # 2단계: 실시간 분석
        logger.info(f"분석 캐시 미스, 실시간 분석 - 회사: {company}")
        request = SimpleCompanySearchRequest(company=company)
        optimized_request = request.to_optimized_news_search_request()
        result = await news_controller.analyze_company_news(optimized_request)
        
        # 3단계: 분석 결과 캐시 저장
        background_tasks.add_task(
            dashboard_controller.set_cache_data,
            cache_key,
            result.dict(),
            expire_minutes=60  # 분석 결과는 1시간 캐시
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Smart company analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 뉴스 분석 중 오류: {str(e)}")

@search_router.post(
    "/batch",
    response_model=List[NewsSearchResponse],
    summary="배치 뉴스 검색",
    description="여러 검색 요청을 동시에 처리합니다. 각각 캐시를 먼저 확인합니다."
)
async def batch_search_news(
    requests: List[NewsSearchRequest],
    background_tasks: BackgroundTasks,
    news_controller: NewsController = Depends(get_news_controller)
):
    """배치 뉴스 검색"""
    try:
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="최대 10개의 요청만 처리 가능")
        
        return await news_controller.batch_search_news(requests)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"배치 검색 중 오류: {str(e)}")

@search_router.get(
    "/trending",
    response_model=TrendingKeywordsResponse,
    summary="트렌딩 키워드",
    description="현재 트렌딩 중인 뉴스 키워드를 조회합니다."
)
async def get_trending_keywords(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    news_controller: NewsController = Depends(get_news_controller)
):
    """트렌딩 키워드 조회"""
    try:
        return await news_controller.get_trending_keywords(category)
    except Exception as e:
        logger.error(f"Trending keywords failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"트렌딩 키워드 조회 중 오류: {str(e)}")

# ============================================================================
# 📊 DASHBOARD ROUTER (캐시 전용 - 백그라운드 데이터)
# ============================================================================

@dashboard_router.get(
    "/status",
    summary="대시보드 전체 상태",
    description="백그라운드 모니터링 시스템의 전체 상태를 조회합니다."
)
async def get_dashboard_status(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """대시보드 전체 상태 조회"""
    return await controller.get_dashboard_status()

@dashboard_router.get(
    "/companies",
    summary="모니터링 회사 목록",
    description="30분마다 자동 분석 중인 회사 목록을 조회합니다."
)
async def get_monitored_companies(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """모니터링 중인 회사 목록"""
    return await controller.get_monitored_companies()

@dashboard_router.get(
    "/companies/{company}/latest",
    summary="회사 최신 분석 결과",
    description="백그라운드에서 수집된 특정 회사의 최신 분석 결과를 조회합니다."
)
async def get_company_latest_analysis(
    company: str = Path(..., description="회사명"),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """특정 회사의 최신 분석 결과"""
    return await controller.get_company_analysis(company)

@dashboard_router.get(
    "/companies/{company}/history",
    summary="회사 분석 히스토리",
    description="특정 회사의 과거 분석 이력을 조회합니다."
)
async def get_company_analysis_history(
    company: str = Path(..., description="회사명"),
    limit: int = Query(20, ge=1, le=50, description="조회할 이력 개수"),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 분석 히스토리"""
    return await controller.get_company_analysis_history(company, limit)

@dashboard_router.post(
    "/companies/{company}/trigger",
    summary="백그라운드 분석 요청",
    description="특정 회사의 백그라운드 분석을 즉시 요청합니다."
)
async def trigger_company_analysis(
    company: str = Path(..., description="회사명"),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """백그라운드 분석 요청"""
    return await controller.request_company_analysis(company)

@dashboard_router.get(
    "/latest",
    summary="모든 회사 최신 결과",
    description="모든 모니터링 회사의 최신 분석 결과를 한 번에 조회합니다."
)
async def get_all_latest_analysis(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """모든 회사의 최신 분석 결과"""
    return await controller.get_all_latest_analysis()

@dashboard_router.get(
    "/cache/info",
    summary="캐시 정보",
    description="현재 Redis 캐시 상태와 통계를 조회합니다."
)
async def get_cache_info(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """캐시 정보 조회"""
    return await controller.get_cache_info()

@dashboard_router.delete(
    "/cache/{company}",
    summary="회사 캐시 삭제",
    description="특정 회사의 모든 캐시 데이터를 삭제합니다."
)
async def clear_company_cache(
    company: str = Path(..., description="회사명"),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 캐시 삭제"""
    return await controller.clear_company_cache(company)

# ============================================================================
# 🛠️ SYSTEM ROUTER (시스템 관리)
# ============================================================================

@system_router.get(
    "/health",
    summary="헬스체크",
    description="전체 서비스의 상태를 확인합니다."
)
async def health_check():
    """시스템 헬스체크"""
    return {
        "status": "healthy",
        "service": "news-service",
        "version": "2.0.0",
        "features": ["smart-search", "dashboard", "cache-optimization"],
        "timestamp": datetime.utcnow().isoformat()
    }

@system_router.post(
    "/test/celery",
    summary="Celery 테스트",
    description="Celery Worker 연결과 작업 처리를 테스트합니다."
)
async def test_celery_connection(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Celery 연결 테스트"""
    return await controller.test_celery_connection()

@system_router.get(
    "/test/result",
    summary="테스트 결과 확인",
    description="Celery 테스트 작업의 결과를 확인합니다."
)
async def get_celery_test_result(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Celery 테스트 결과"""
    return await controller.get_test_result()

# ============================================================================
# 메인 라우터 (모든 하위 라우터 통합)
# ============================================================================

# 메인 통합 라우터
main_router = APIRouter(prefix="/api/v1")
main_router.include_router(search_router)
main_router.include_router(dashboard_router)
main_router.include_router(system_router)

# 루트 레벨 헬스체크 (하위 호환성)
@main_router.get("/health")
async def root_health_check():
    """루트 헬스체크 (하위 호환성)"""
    return await health_check()

# 유틸리티 함수들
async def _log_search_request(request_type: str, query: str, request_data: dict):
    """검색 요청 로깅"""
    logger.info(f"Search request - Type: {request_type}, Query: {query}")

async def _log_batch_request(request_type: str, queries: List[str]):
    """배치 요청 로깅"""
    logger.info(f"Batch request - Type: {request_type}, Queries: {queries}") 