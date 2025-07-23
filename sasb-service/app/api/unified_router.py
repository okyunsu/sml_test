"""SASB 서비스 통합 API 라우터 - News Service와 유사한 구조"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Path, Query
from datetime import datetime
import os
import sys

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# ✅ 공통 감정 변환 모듈 사용
from shared.services.sentiment_helper import SentimentConverter

from app.domain.controller.sasb_controller import SASBController
from app.domain.controller.dashboard_controller import DashboardController
from app.domain.model.sasb_dto import (
    NewsAnalysisRequest, NewsAnalysisResult, AnalyzedNewsArticle
)
from app.core.dependencies import get_dependency, DependencyContainer
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# ✅ 공통 모듈 사용 (기존 함수 제거)
convert_sentiment_label = SentimentConverter.convert_sentiment_label

def convert_articles_sentiment(articles: List[dict]) -> List[dict]:
    """기사 리스트의 sentiment를 모두 변환"""
    converted_articles = []
    
    for article in articles:
        # 기사 복사
        converted_article = dict(article)
        
        # sentiment 필드가 있으면 변환
        if "sentiment" in converted_article and isinstance(converted_article["sentiment"], dict):
            sentiment_data = converted_article["sentiment"]
            if "sentiment" in sentiment_data:
                original_sentiment = sentiment_data["sentiment"]
                converted_sentiment = convert_sentiment_label(original_sentiment)
                
                # 변환된 sentiment로 업데이트
                sentiment_data["sentiment"] = converted_sentiment
                sentiment_data["original_label"] = original_sentiment  # 원본 라벨 보관
                
                logger.debug(f"Sentiment 변환: {original_sentiment} → {converted_sentiment}")
        
        converted_articles.append(converted_article)
    
    return converted_articles

# 의존성 주입 함수들
def get_sasb_controller(
    container: DependencyContainer = Depends(get_dependency)
) -> SASBController:
    """SASBController 의존성 주입"""
    return container.get("sasb_controller")

def get_dashboard_controller(
    container: DependencyContainer = Depends(get_dependency)
) -> DashboardController:
    """DashboardController 의존성 주입"""
    return container.get("dashboard_controller")

# ============================================================================
# 🔗 프론트엔드 핵심 API (Gateway 호환)
# ============================================================================

# 프론트엔드 연결용 핵심 라우터
frontend_router = APIRouter(prefix="/api/v1", tags=["🎨 SASB Frontend API"])

@frontend_router.post(
    "/analyze/company-sasb",
    response_model=NewsAnalysisResult,
    summary="회사 + SASB 키워드 조합 뉴스 분석",
    description="특정 회사와 SASB 키워드 조합으로 뉴스 분석"
)
async def analyze_company_sasb_news(
    company_name: str = Query(..., description="분석할 회사명"),
    sasb_keywords: Optional[List[str]] = Query(None, description="SASB 키워드 리스트 (선택사항)"),
    max_results: int = Query(100, description="수집할 최대 뉴스 개수"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    sasb_controller: SASBController = Depends(get_sasb_controller),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 + SASB 토픽 조합 뉴스 분석"""
    try:
        # 1단계: 캐시 확인
        cache_key = f"company_sasb_analysis:{company_name}"
        cached_result = await dashboard_controller.get_cache_data(cache_key)
        
        if cached_result:
            logger.info(f"캐시 히트 - 회사+SASB: {company_name}")
            return NewsAnalysisResult(**cached_result)
        
        # 2단계: 실시간 분석
        logger.info(f"캐시 미스, 실시간 분석 - 회사+SASB: {company_name}")
        result = await sasb_controller.analyze_company_sasb_news(
            company_name=company_name,
            sasb_keywords=sasb_keywords,
            max_results=max_results
        )
        
        # 3단계: 캐시 저장 (백그라운드)
        background_tasks.add_task(
            dashboard_controller.set_cache_data,
            cache_key, 
            result.dict(),
            expire_minutes=60  # SASB 분석은 1시간 캐시
        )
        
        return result
        
    except Exception as e:
        logger.error(f"회사+SASB 뉴스 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사+SASB 뉴스 분석 중 오류: {str(e)}")

@frontend_router.post(
    "/analyze/sasb-only",
    response_model=NewsAnalysisResult,
    summary="SASB 토픽 전용 뉴스 분석",
    description="SASB 키워드만으로 뉴스 검색 및 분석 (회사명 없음)"
)
async def analyze_sasb_only_news(
    sasb_keywords: Optional[List[str]] = Query(None, description="SASB 키워드 목록 (미지정시 기본값 사용)"),
    max_results: int = Query(100, description="수집할 최대 뉴스 개수"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    sasb_controller: SASBController = Depends(get_sasb_controller),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """SASB 토픽 전용 뉴스 분석"""
    try:
        # 1단계: 캐시 확인
        cache_key = f"sasb_only_analysis:{hash(str(sasb_keywords))}"
        cached_result = await dashboard_controller.get_cache_data(cache_key)
        
        if cached_result:
            logger.info(f"캐시 히트 - SASB 전용")
            return NewsAnalysisResult(**cached_result)
        
        # 2단계: 실시간 분석
        logger.info(f"캐시 미스, 실시간 분석 - SASB 전용")
        result = await sasb_controller.analyze_sasb_only_news(
            sasb_keywords=sasb_keywords,
            max_results=max_results
        )
        
        # 3단계: 캐시 저장 (백그라운드)
        background_tasks.add_task(
            dashboard_controller.set_cache_data,
            cache_key,
            result.dict(),
            expire_minutes=30  # SASB 전용은 30분 캐시
        )
        
        return result
        
    except Exception as e:
        logger.error(f"SASB 전용 뉴스 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SASB 전용 뉴스 분석 중 오류: {str(e)}")

@frontend_router.get(
    "/health",
    summary="헬스체크",
    description="SASB 서비스 상태 확인"
)
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "sasb-service",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "🔍 회사 + SASB 키워드 조합 분석",
            "📊 SASB 전용 키워드 분석",
            "💾 Redis 캐시 시스템",
            "🔄 백그라운드 자동 분석"
        ]
    }

# ============================================================================
# 📊 대시보드 관리 API
# ============================================================================

dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["📊 SASB Dashboard"])

@dashboard_router.get(
    "/status",
    summary="대시보드 전체 상태",
    description="SASB 시스템 전체 상태 및 Redis 연결 확인"
)
async def get_dashboard_status(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """대시보드 전체 상태"""
    try:
        return await dashboard_controller.get_system_status()
    except Exception as e:
        logger.error(f"대시보드 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대시보드 상태 조회 중 오류: {str(e)}")

@dashboard_router.get(
    "/companies",
    summary="모니터링 회사 목록",
    description="현재 SASB 모니터링 중인 회사 목록"
)
async def get_monitored_companies(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """모니터링 중인 회사 목록"""
    return {
        "companies": ["두산퓨얼셀", "LS ELECTRIC"],
        "total_count": 2,
        "last_updated": datetime.now().isoformat()
    }

@dashboard_router.get(
    "/sasb-news",
    response_model=NewsAnalysisResult,
    summary="SASB 뉴스 분석 결과 조회",
    description="SASB 키워드로 분석된 최신 뉴스 결과 조회 (Worker 결과 우선, 처음 대시보드용)"
)
async def get_sasb_news_analysis(
    max_results: int = Query(100, description="반환할 최대 뉴스 개수"),
    force_realtime: bool = Query(False, description="실시간 분석 강제 실행 (Worker 결과 무시)"),
    sasb_keywords: Optional[List[str]] = Query(None, description="SASB 키워드 목록 (미지정시 기본값 사용)"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller),
    sasb_controller: SASBController = Depends(get_sasb_controller)
):
    """SASB 뉴스 분석 결과 조회 (Worker 결과 우선, 처음 대시보드용)"""
    try:
        # 🔄 1단계: Worker 결과 우선 확인 (force_realtime=False일 때)
        if not force_realtime:
            worker_articles = await dashboard_controller.get_cache_data("latest_sasb_renewable_analysis")
            
            if worker_articles:
                logger.info("✅ Worker에서 처리된 SASB 뉴스 결과 반환 (빠른 응답)")
                
                # Worker 결과는 기사 리스트이므로 NewsAnalysisResult 형태로 변환
                if isinstance(worker_articles, list):
                    # 결과 개수 제한 적용
                    limited_articles = []
                    for i, article in enumerate(worker_articles):
                        if i >= max_results:
                            break
                        limited_articles.append(article)
                    
                    # 🔄 Sentiment 변환 적용 (LABEL_X → 긍정/부정/중립)
                    converted_articles = convert_articles_sentiment(limited_articles)
                    logger.info(f"대시보드 Worker 결과 {len(converted_articles)}개 기사의 sentiment 변환 완료")
                    
                    # dict를 AnalyzedNewsArticle 객체로 변환
                    article_objects = []
                    for article_dict in converted_articles:
                        try:
                            article_obj = AnalyzedNewsArticle(**article_dict)
                            article_objects.append(article_obj)
                        except Exception as e:
                            logger.warning(f"대시보드 기사 객체 변환 실패: {e}")
                            continue
                    
                    # NewsAnalysisResult 형태로 래핑
                    result = NewsAnalysisResult(
                        task_id="worker_sasb_dashboard",
                        status="completed",
                        searched_keywords=["SASB 키워드 (Worker 처리)"],
                        total_articles_found=len(article_objects),
                        analyzed_articles=article_objects,
                        company_name=None,
                        analysis_type="sasb_only_worker"
                    )
                    
                    return result
        
        # 🔍 2단계: 실시간 분석 캐시 확인
        cache_key = f"sasb_only_analysis:{hash(str(sasb_keywords))}"
        cached_result = await dashboard_controller.get_cache_data(cache_key)
        
        if cached_result and not force_realtime:
            logger.info("💾 캐시된 실시간 SASB 뉴스 분석 결과 반환")
            result = NewsAnalysisResult(**cached_result)
            
            # 결과 개수 제한 적용
            if result.analyzed_articles and len(result.analyzed_articles) > max_results:
                result.analyzed_articles = result.analyzed_articles[:max_results]
                result.total_articles_found = len(result.analyzed_articles)
            
            return result
        
        # ⏱️ 3단계: 실시간 분석 실행 (최후 수단)
        logger.info("⚡ Worker 결과 없음, 실시간 SASB 뉴스 분석 실행 (느림)")
        result = await sasb_controller.analyze_sasb_only_news(
            sasb_keywords=sasb_keywords,
            max_results=max_results
        )
        
        # 실시간 분석 결과에 메타데이터 추가
        result_dict = result.dict()
        result_dict["source"] = "realtime_analysis"
        result_dict["analysis_type"] = "sasb_only_realtime"
        
        # 결과를 캐시에 저장 (30분)
        await dashboard_controller.set_cache_data(
            cache_key,
            result_dict,
            expire_minutes=30
        )
        
        return result
        
    except Exception as e:
        logger.error(f"SASB 뉴스 분석 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SASB 뉴스 분석 조회 중 오류: {str(e)}")

@dashboard_router.get(
    "/companies/{company}/latest",
    summary="회사 최신 SASB 분석 결과",
    description="특정 회사의 최신 SASB 분석 결과 조회"
)
async def get_company_latest_analysis(
    company: str = Path(..., description="회사명"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 최신 분석 결과"""
    try:
        # Worker에서 사용하는 키와 동일하게 변경
        cache_key = f"latest_company_sasb_analysis:{company}"
        result = await dashboard_controller.get_cache_data(cache_key)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"{company}의 분석 결과를 찾을 수 없습니다.")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회사 분석 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 결과 조회 중 오류: {str(e)}")

# ============================================================================
# 🗄️ 캐시 관리 API
# ============================================================================

cache_router = APIRouter(prefix="/api/v1/cache", tags=["🗄️ SASB Cache"])

@cache_router.get(
    "/info",
    summary="캐시 정보 조회",
    description="Redis 캐시 상태 및 통계 정보"
)
async def get_cache_info(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """캐시 정보 조회"""
    try:
        return await dashboard_controller.get_cache_info()
    except Exception as e:
        logger.error(f"캐시 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캐시 정보 조회 중 오류: {str(e)}")

@cache_router.delete(
    "/company/{company}",
    summary="회사 캐시 삭제",
    description="특정 회사의 SASB 캐시 데이터 삭제"
)
async def clear_company_cache(
    company: str = Path(..., description="회사명"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """회사 캐시 삭제"""
    try:
        # Worker에서 사용하는 키들과 일치하도록 수정
        cache_keys = [
            f"company_sasb_analysis:{company}",
            f"latest_company_sasb_analysis:{company}",  # Worker에서 실제 사용하는 키
            f"latest_companies_renewable_analysis:{company}"  # 이전 키 (혹시 남아있을 수 있는 캐시)
        ]
        
        deleted_count = 0
        for key in cache_keys:
            if await dashboard_controller.delete_cache_data(key):
                deleted_count += 1
        
        return {
            "message": f"{company}의 캐시가 삭제되었습니다.",
            "deleted_keys": deleted_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"캐시 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캐시 삭제 중 오류: {str(e)}")

# ============================================================================
# 🛠️ 시스템 관리 API
# ============================================================================

system_router = APIRouter(prefix="/api/v1/system", tags=["🛠️ SASB System"])

@system_router.get(
    "/health",
    summary="시스템 헬스체크",
    description="전체 SASB 시스템 상태 확인"
)
async def system_health_check():
    """시스템 헬스체크"""
    return {
        "status": "healthy",
        "service": "sasb-service",
        "version": "2.0.0",
        "components": {
            "api": "healthy",
            "redis": "healthy",
            "celery": "healthy",
            "ml_models": "healthy"
        },
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# 🔄 Worker 모니터링 API
# ============================================================================

worker_router = APIRouter(prefix="/api/v1/workers", tags=["🔄 SASB Workers"])

@worker_router.get(
    "/status",
    summary="Worker 전체 상태",
    description="Celery Worker 상태 및 실행 중인 작업 확인"
)
async def get_worker_status(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """Worker 전체 상태 조회"""
    try:
        # Worker 작업 상태 확인
        status_keys = [
            "status:combined_keywords_analysis",
            "status:company_combined_keywords_analysis"
        ]
        
        worker_status = {}
        for key in status_keys:
            status = await dashboard_controller.get_cache_data(key)
            task_name = key.replace("status:", "")
            worker_status[task_name] = status or "IDLE"
        
        # 다음 실행 예정 시간 계산
        now = datetime.now()
        next_runs = {
            "combined_keywords_analysis": _calculate_next_cron(now, "5,35 * * * *"),
            "company_combined_keywords_analysis": _calculate_next_cron(now, "10,40 * * * *")
        }
        
        return {
            "status": "active",
            "timestamp": now.isoformat(),
            "tasks": worker_status,
            "next_scheduled_runs": next_runs,
            "total_active_tasks": sum(1 for status in worker_status.values() if status == "IN_PROGRESS")
        }
        
    except Exception as e:
        logger.error(f"Worker 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Worker 상태 조회 중 오류: {str(e)}")

@worker_router.get(
    "/results/sasb-news",
    response_model=NewsAnalysisResult,
    summary="Worker 처리 SASB 뉴스 결과",
    description="Worker에서 백그라운드로 처리한 SASB 뉴스 분석 결과 조회"
)
async def get_worker_sasb_results(
    max_results: int = Query(100, description="반환할 최대 뉴스 개수"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """Worker에서 처리한 SASB 뉴스 결과 조회"""
    try:
        # Worker에서 저장한 SASB 전용 분석 결과 조회 (기사 리스트 형태)
        worker_articles = await dashboard_controller.get_cache_data("latest_sasb_renewable_analysis")
        
        if not worker_articles:
            raise HTTPException(
                status_code=404, 
                detail="Worker에서 처리한 SASB 뉴스 결과가 없습니다. Worker가 실행될 때까지 기다려주세요."
            )
        
        # Worker 결과는 기사 리스트이므로 NewsAnalysisResult 형태로 변환
        if isinstance(worker_articles, list):
            # 결과 개수 제한 적용
            articles_count = len(worker_articles)
            limited_articles = []
            for i, article in enumerate(worker_articles):
                if i >= max_results:
                    break
                limited_articles.append(article)
            
            # 🔄 Sentiment 변환 적용 (LABEL_X → 긍정/부정/중립)
            converted_articles = convert_articles_sentiment(limited_articles)
            logger.info(f"Worker 결과 {len(converted_articles)}개 기사의 sentiment 변환 완료")
            
            # dict를 AnalyzedNewsArticle 객체로 변환
            article_objects = []
            for article_dict in converted_articles:
                try:
                    article_obj = AnalyzedNewsArticle(**article_dict)
                    article_objects.append(article_obj)
                except Exception as e:
                    logger.warning(f"기사 객체 변환 실패: {e}")
                    continue
            
            # NewsAnalysisResult 형태로 래핑
            result = NewsAnalysisResult(
                task_id="worker_sasb_analysis",
                status="completed",
                searched_keywords=["SASB 키워드 (Worker 처리)"],
                total_articles_found=len(article_objects),
                analyzed_articles=article_objects,
                company_name=None,
                analysis_type="sasb_only_worker"
            )
            
            return result
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Worker 결과 형태가 올바르지 않습니다. 타입: {type(worker_articles)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Worker SASB 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Worker SASB 결과 조회 중 오류: {str(e)}")

@worker_router.get(
    "/results/companies",
    summary="Worker 처리 회사별 분석 결과",
    description="Worker에서 백그라운드로 처리한 회사별 분석 결과 목록"
)
async def get_worker_company_results(
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """Worker에서 처리한 회사별 분석 결과 조회"""
    try:
        # Worker에서 저장한 회사별 분석 결과 조회
        worker_result = await dashboard_controller.get_cache_data("latest_companies_renewable_analysis")
        
        if not worker_result:
            raise HTTPException(
                status_code=404,
                detail="Worker에서 처리한 회사별 분석 결과가 없습니다. Worker가 실행될 때까지 기다려주세요."
            )
        
        # 메타데이터 추가
        result = {
            "source": "worker_background",
            "last_updated": worker_result.get("timestamp", datetime.now().isoformat()),
            "total_companies": len(worker_result.get("companies", [])),
            "companies_data": worker_result
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Worker 회사별 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Worker 회사별 결과 조회 중 오류: {str(e)}")

@worker_router.get(
    "/results/combined-keywords",
    response_model=NewsAnalysisResult,
    summary="🎯 조합 검색 결과 조회",
    description="(산업 키워드) AND (SASB 이슈 키워드) 조합 검색으로 수집된 정확도 높은 뉴스"
)
async def get_combined_keywords_results(
    max_results: int = Query(100, description="반환할 최대 뉴스 개수"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """🎯 조합 검색 결과 조회 - 관련성 높은 신재생에너지 뉴스만"""
    try:
        # Worker에서 저장한 조합 검색 결과 조회
        worker_articles = await dashboard_controller.get_cache_data("latest_combined_keywords_analysis")
        
        if not worker_articles:
            raise HTTPException(
                status_code=404, 
                detail="🎯 조합 검색 결과가 없습니다. Worker가 실행될 때까지 기다려주세요."
            )
        
        # Worker 결과는 기사 리스트이므로 NewsAnalysisResult 형태로 변환
        if isinstance(worker_articles, list):
            # 결과 개수 제한 적용
            articles_count = len(worker_articles)
            limited_articles = []
            for i, article in enumerate(worker_articles):
                if i >= max_results:
                    break
                limited_articles.append(article)
            
            # 🔄 Sentiment 변환 적용 (LABEL_X → 긍정/부정/중립)
            converted_articles = convert_articles_sentiment(limited_articles)
            logger.info(f"🎯 조합 검색 결과 {len(converted_articles)}개 기사의 sentiment 변환 완료")
            
            # dict를 AnalyzedNewsArticle 객체로 변환
            article_objects = []
            for article_dict in converted_articles:
                try:
                    article_obj = AnalyzedNewsArticle(**article_dict)
                    article_objects.append(article_obj)
                except Exception as e:
                    logger.warning(f"조합 검색 기사 객체 변환 실패: {e}")
                    continue
            
            # NewsAnalysisResult 형태로 래핑
            result = NewsAnalysisResult(
                task_id="combined_keywords_analysis",
                status="completed",
                searched_keywords=["🎯 산업+이슈 조합 키워드"],
                total_articles_found=len(article_objects),
                analyzed_articles=article_objects,
                company_name=None,
                analysis_type="combined_keywords"
            )
            
            return result
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"조합 검색 결과 형태가 올바르지 않습니다. 타입: {type(worker_articles)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🎯 조합 검색 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조합 검색 결과 조회 중 오류: {str(e)}")

@worker_router.get(
    "/results/company-combined/{company}",
    response_model=NewsAnalysisResult,
    summary="🎯 회사별 조합 검색 결과 조회",
    description="특정 회사 + (산업 키워드) AND (SASB 이슈 키워드) 조합 검색 결과"
)
async def get_company_combined_results(
    company: str = Path(..., description="회사명"),
    max_results: int = Query(100, description="반환할 최대 뉴스 개수"),
    dashboard_controller: DashboardController = Depends(get_dashboard_controller)
):
    """🎯 회사별 조합 검색 결과 조회"""
    try:
        # Worker에서 저장한 회사별 조합 검색 결과 조회
        cache_key = f"latest_company_combined_analysis:{company}"
        worker_articles = await dashboard_controller.get_cache_data(cache_key)
        
        if not worker_articles:
            raise HTTPException(
                status_code=404, 
                detail=f"🎯 {company}의 조합 검색 결과가 없습니다. Worker가 실행될 때까지 기다려주세요."
            )
        
        # Worker 결과는 기사 리스트이므로 NewsAnalysisResult 형태로 변환
        if isinstance(worker_articles, list):
            # 결과 개수 제한 적용
            limited_articles = []
            for i, article in enumerate(worker_articles):
                if i >= max_results:
                    break
                limited_articles.append(article)
            
            # 🔄 Sentiment 변환 적용
            converted_articles = convert_articles_sentiment(limited_articles)
            logger.info(f"🎯 {company} 조합 검색 결과 {len(converted_articles)}개 기사의 sentiment 변환 완료")
            
            # dict를 AnalyzedNewsArticle 객체로 변환
            article_objects = []
            for article_dict in converted_articles:
                try:
                    article_obj = AnalyzedNewsArticle(**article_dict)
                    article_objects.append(article_obj)
                except Exception as e:
                    logger.warning(f"{company} 조합 검색 기사 객체 변환 실패: {e}")
                    continue
            
            # NewsAnalysisResult 형태로 래핑
            result = NewsAnalysisResult(
                task_id=f"company_combined_analysis_{company}",
                status="completed",
                searched_keywords=[f"🎯 {company}+산업+이슈 조합 키워드"],
                total_articles_found=len(article_objects),
                analyzed_articles=article_objects,
                company_name=company,
                analysis_type="company_combined_keywords"
            )
            
            return result
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"{company} 조합 검색 결과 형태가 올바르지 않습니다. 타입: {type(worker_articles)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🎯 {company} 조합 검색 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{company} 조합 검색 결과 조회 중 오류: {str(e)}")

@worker_router.get(
    "/schedule",
    summary="Worker 스케줄 정보",
    description="예약된 Worker 작업 스케줄 및 다음 실행 시간"
)
async def get_worker_schedule():
    """Worker 스케줄 정보 조회"""
    try:
        now = datetime.now()
        
        schedule_info = {
            "current_time": now.isoformat(),
            "scheduled_tasks": [
                {
                    "name": "🎯 조합 키워드 분석",
                    "task_id": "run_combined_keywords_analysis",
                    "schedule": "시작 후 1분, 이후 10분마다 (1,11,21,31,41,51분)",
                    "cron": "1,11,21,31,41,51 * * * *",
                    "next_run": _calculate_next_cron(now, "1,11,21,31,41,51 * * * *"),
                    "description": "(산업 키워드) AND (SASB 이슈 키워드) 조합 검색으로 정확도 높은 뉴스 수집"
                },
                {
                    "name": "🎯 회사별 조합 키워드 분석", 
                    "task_id": "run_company_combined_keywords_analysis",
                    "schedule": "시작 후 3분, 이후 10분마다 (3,13,23,33,43,53분)",
                    "cron": "3,13,23,33,43,53 * * * *", 
                    "next_run": _calculate_next_cron(now, "3,13,23,33,43,53 * * * *"),
                    "description": "회사 + (산업 키워드) AND (SASB 이슈 키워드) 조합으로 회사별 정확도 높은 뉴스 수집"
                }
            ]
        }
        
        return schedule_info
        
    except Exception as e:
        logger.error(f"Worker 스케줄 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Worker 스케줄 조회 중 오류: {str(e)}")

def _calculate_next_cron(current_time: datetime, cron_pattern: str) -> str:
    """크론 패턴으로 다음 실행 시간 계산 (간단한 구현)"""
    if "5,35" in cron_pattern:
        # 매 시간 5분, 35분에 실행
        minutes = current_time.minute
        if minutes < 5:
            next_time = current_time.replace(minute=5, second=0, microsecond=0)
        elif minutes < 35:
            next_time = current_time.replace(minute=35, second=0, microsecond=0)
        else:
            # 다음 시간 5분
            next_time = current_time.replace(hour=current_time.hour + 1, minute=5, second=0, microsecond=0)
    elif "10,40" in cron_pattern:
        # 매 시간 10분, 40분에 실행
        minutes = current_time.minute
        if minutes < 10:
            next_time = current_time.replace(minute=10, second=0, microsecond=0)
        elif minutes < 40:
            next_time = current_time.replace(minute=40, second=0, microsecond=0)
        else:
            # 다음 시간 10분
            next_time = current_time.replace(hour=current_time.hour + 1, minute=10, second=0, microsecond=0)
    else:
        next_time = current_time
    
    return next_time.isoformat()

# ============================================================================
# 🔗 라우터 등록
# ============================================================================

# 메인 라우터 (간단한 구조)
main_router = APIRouter()
main_router.include_router(frontend_router)
main_router.include_router(dashboard_router)
main_router.include_router(cache_router)
main_router.include_router(system_router)
main_router.include_router(worker_router)

 