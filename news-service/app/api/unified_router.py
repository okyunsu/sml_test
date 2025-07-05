"""프론트엔드 연결용 핵심 API 라우터"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Path, Query
from datetime import datetime

from app.domain.controller.news_controller import NewsController
from app.domain.controller.dashboard_controller import DashboardController
from app.domain.model.news_dto import (
    NewsSearchRequest, NewsSearchResponse, NewsAnalysisResponse, SimpleCompanySearchRequest
)
from app.core.dependencies import get_dependency, DependencyContainer, get_settings
from app.config.settings import Settings
import logging
import httpx

logger = logging.getLogger(__name__)

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
# 🔗 프론트엔드 핵심 API (Gateway 호환)
# ============================================================================

# 프론트엔드 연결용 핵심 라우터
frontend_router = APIRouter(tags=["🎨 Frontend API"])

@frontend_router.post(
    "/search",
    response_model=NewsSearchResponse,
    summary="뉴스 검색",
    description="일반 뉴스 검색 - 캐시 우선, 실시간 폴백"
)
async def search_news(
    request: NewsSearchRequest,
    background_tasks: BackgroundTasks,
    news_controller: NewsController = Depends(get_news_controller),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """뉴스 검색"""
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
        logger.error(f"뉴스 검색 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 검색 중 오류: {str(e)}")

@frontend_router.post(
    "/companies/{company}",
    response_model=NewsSearchResponse,
    summary="회사 뉴스 검색",
    description="회사별 뉴스 검색 - 캐시 우선, 실시간 폴백"
)
async def search_company_news(
    background_tasks: BackgroundTasks,
    company: str = Path(..., description="회사명"),
    news_controller: NewsController = Depends(get_news_controller),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 뉴스 검색"""
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
        logger.error(f"회사 뉴스 검색 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 뉴스 검색 중 오류: {str(e)}")

@frontend_router.post(
    "/companies/{company}/analyze",
    response_model=NewsAnalysisResponse,
    summary="회사 뉴스 분석",
    description="회사 뉴스 AI 분석 - ESG, 감정분석, 키워드 추출"
)
async def analyze_company_news(
    background_tasks: BackgroundTasks,
    company: str = Path(..., description="회사명"),
    news_controller: NewsController = Depends(get_news_controller),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 뉴스 분석"""
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
        logger.error(f"회사 뉴스 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 뉴스 분석 중 오류: {str(e)}")


async def send_to_n8n(webhook_url: str, data: dict):
    """n8n 웹훅으로 비동기 POST 요청을 보냅니다."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=data, timeout=10.0)
            response.raise_for_status()  # 2xx 외의 응답 코드는 예외 발생
        logger.info(f"n8n 웹훅 호출 성공: {response.status_code}, 응답: {response.text}")
    except httpx.RequestError as e:
        logger.error(f"n8n 웹훅 연결 실패: {e.request.method} {e.request.url} - {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"n8n 웹훅 응답 오류: {e.response.status_code} - {e.response.text}")


@frontend_router.post(
    "/companies/{company}/export",
    status_code=202,
    summary="회사 뉴스 분석 결과 엑셀(Google Sheets)로 내보내기",
    description="분석된 데이터를 n8n을 통해 Google Sheets로 전송합니다."
)
async def export_company_news_to_sheet(
    background_tasks: BackgroundTasks,
    company: str = Path(..., description="회사명"),
    news_controller: NewsController = Depends(get_news_controller),
    settings: Settings = Depends(get_settings)
):
    """회사 뉴스 분석 결과를 n8n 웹훅으로 전송"""
    if not settings.n8n_export_webhook_url:
        logger.error("N8N_EXPORT_WEBHOOK_URL이 설정되지 않았습니다.")
        raise HTTPException(
            status_code=501,
            detail="서버에 내보내기 기능이 설정되지 않았거나 비활성화되었습니다."
        )

    try:
        # 1. 기존 분석 로직을 호출하여 데이터 생성
        logger.info(f"'{company}' 분석 데이터 생성 중 for export...")
        request = SimpleCompanySearchRequest(company=company)
        optimized_request = request.to_optimized_news_search_request()
        analysis_result = await news_controller.analyze_company_news(optimized_request)

        # 2. n8n 웹훅 호출 (백그라운드에서 실행하여 응답을 빠르게)
        logger.info(f"n8n 웹훅으로 데이터 전송 요청: {settings.n8n_export_webhook_url}")
        background_tasks.add_task(
            send_to_n8n,
            settings.n8n_export_webhook_url,
            analysis_result.dict()
        )

        return {"status": "accepted", "message": f"'{company}' 데이터의 Google Sheets 내보내기 요청이 접수되었습니다."}

    except Exception as e:
        logger.error(f"회사 뉴스 내보내기 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터 내보내기 중 오류 발생: {str(e)}")


@frontend_router.get(
    "/health",
    summary="헬스체크",
    description="서비스 상태 확인"
)
async def health_check():
    """서비스 헬스체크"""
    return {
        "status": "healthy",
        "service": "news-service",
        "version": "2.0.0-frontend",
        "features": ["news-search", "company-search", "news-analysis"],
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# 📊 대시보드 관리 API (캐시 포함)
# ============================================================================

dashboard_router = APIRouter(prefix="/dashboard", tags=["📊 Dashboard & Cache Management"])

@dashboard_router.get(
    "/status",
    summary="대시보드 전체 상태",
    description="시스템 전체 상태 및 Redis 연결 확인"
)
async def get_dashboard_status(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """대시보드 전체 상태 조회"""
    return await dashboard_controller.get_dashboard_status()

@dashboard_router.get(
    "/companies",
    summary="모니터링 회사 목록",
    description="현재 모니터링 중인 회사 목록"
)
async def get_monitored_companies(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """모니터링 중인 회사 목록 조회"""
    return await dashboard_controller.get_monitored_companies()

@dashboard_router.get(
    "/companies/{company}",
    summary="회사 최신 분석 결과",
    description="특정 회사의 최신 분석 결과 조회"
)
async def get_company_analysis(
    company: str = Path(..., description="회사명"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """특정 회사의 최신 분석 결과 조회"""
    return await dashboard_controller.get_company_analysis(company)

@dashboard_router.get(
    "/companies/{company}/history",
    summary="회사 분석 히스토리",
    description="특정 회사의 분석 히스토리"
)
async def get_company_analysis_history(
    company: str = Path(..., description="회사명"),
    limit: int = Query(20, description="조회할 히스토리 개수"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """특정 회사의 분석 히스토리 조회"""
    return await dashboard_controller.get_company_analysis_history(company, limit)

@dashboard_router.get(
    "/analysis/latest",
    summary="모든 회사 최신 분석",
    description="모든 회사의 최신 분석 결과"
)
async def get_all_latest_analysis(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """모든 회사의 최신 분석 결과 조회"""
    return await dashboard_controller.get_all_latest_analysis()

@dashboard_router.post(
    "/companies/{company}/analyze",
    summary="수동 분석 요청",
    description="특정 회사의 수동 분석 요청"
)
async def request_company_analysis(
    company: str = Path(..., description="회사명"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """특정 회사의 수동 분석 요청"""
    return await dashboard_controller.request_company_analysis(company)

# ============================================================================
# 🗄️ 캐시 관리 API
# ============================================================================

cache_router = APIRouter(prefix="/cache", tags=["🗄️ Cache Management"])

@cache_router.get(
    "/info",
    summary="캐시 정보 조회",
    description="Redis 캐시 상태 및 통계 정보"
)
async def get_cache_info(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """캐시 정보 조회"""
    return await dashboard_controller.get_cache_info()

@cache_router.delete(
    "/{company}",
    summary="회사 캐시 삭제",
    description="특정 회사의 캐시 데이터 삭제"
)
async def clear_company_cache(
    company: str = Path(..., description="회사명"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """특정 회사의 캐시 삭제"""
    return await dashboard_controller.clear_company_cache(company)

# ============================================================================
# 🔧 시스템 관리 API
# ============================================================================

system_router = APIRouter(prefix="/system", tags=["🔧 System Management"])

@system_router.get(
    "/health",
    summary="시스템 헬스체크",
    description="전체 시스템 상태 확인"
)
async def system_health_check():
    """시스템 헬스체크"""
    return {
        "status": "healthy",
        "service": "news-service",
        "version": "2.0.0-complete",
        "features": [
            "news-search", "company-search", "news-analysis",
            "dashboard", "cache-management", "system-monitoring"
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "healthy",
            "cache": "redis-enabled",
            "workers": "celery-enabled",
            "ml": "inference-ready"
        }
    }

@system_router.get(
    "/celery/test",
    summary="Celery 연결 테스트",
    description="Celery Worker 연결 상태 테스트"
)
async def test_celery_connection(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """Celery Worker 연결 테스트"""
    return await dashboard_controller.test_celery_connection()

@system_router.get(
    "/celery/result",
    summary="Celery 테스트 결과",
    description="Celery 테스트 작업 결과 확인"
)
async def get_test_result(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """Celery 테스트 결과 확인"""
    return await dashboard_controller.get_test_result()

# ============================================================================
# 메인 라우터 (간단한 구조)
# ============================================================================

# 메인 통합 라우터 - 간단한 경로 (Gateway 최적화)
main_router = APIRouter()
main_router.include_router(frontend_router)
main_router.include_router(dashboard_router)
main_router.include_router(cache_router)
main_router.include_router(system_router)

# 기존 호환성을 위한 API v1 라우터
legacy_router = APIRouter(prefix="/api/v1")
legacy_router.include_router(frontend_router)
legacy_router.include_router(dashboard_router)
legacy_router.include_router(cache_router)
legacy_router.include_router(system_router)

# 루트 레벨 헬스체크 (하위 호환성)
@main_router.get("/health")
async def root_health_check():
    """루트 헬스체크"""
    return await health_check()

# API v1 레벨 헬스체크 (하위 호환성)  
@legacy_router.get("/health")
async def legacy_health_check():
    """레거시 API 헬스체크"""
    return await health_check() 