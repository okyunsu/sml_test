from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from ..domain.controller.news_controller import NewsController
from ..domain.model.news_dto import (
    NewsSearchRequest, NewsSearchResponse, ErrorResponse, CompanyNewsRequest,
    TrendingKeywordsResponse, NewsAnalysisResponse, SimpleCompanySearchRequest
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/news", tags=["news"])

def get_news_controller() -> NewsController:
    """NewsController 의존성 주입"""
    return NewsController()

# === 간소화된 엔드포인트 (추천) ===

@router.post(
    "/company/simple",
    response_model=NewsSearchResponse,
    summary="간소화된 회사 뉴스 검색",
    description="""
    회사명만 입력하면 최적화된 설정으로 뉴스를 검색합니다.
    
    **최적화된 고정 설정:**
    - 검색 결과: 100개
    - 정렬: 정확도 순 (관련성 높은 뉴스 우선)
    - 검색 시작 위치: 1 (가장 관련성 높은 뉴스부터)
    - 중복 제거: 활성화
    - 유사도 임계값: 0.75
    
    **사용 예시:**
    ```json
    {
        "company": "삼성전자"
    }
    ```
    """,
    responses={
        200: {"description": "뉴스 검색 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"}
    }
)
async def search_company_news_simple(
    request: SimpleCompanySearchRequest,
    background_tasks: BackgroundTasks,
    controller: NewsController = Depends(get_news_controller)
):
    """
    간소화된 회사별 뉴스 검색 - 회사명만 입력하면 최적화된 설정으로 검색
    
    Args:
        request: 간소화된 검색 요청 (회사명만 포함)
        background_tasks: 백그라운드 작업
        controller: 뉴스 컨트롤러
        
    Returns:
        NewsSearchResponse: 뉴스 검색 결과
    """
    try:
        # 최적화된 검색 요청으로 변환
        optimized_request = request.to_optimized_news_search_request()
        
        # 백그라운드에서 검색 로그 기록
        background_tasks.add_task(
            _log_search_request, 
            "simple_company_search", 
            request.company,
            optimized_request.dict()
        )
        
        # 뉴스 검색 실행
        return await controller.search_news(optimized_request)
        
    except Exception as e:
        logger.error(f"Simple company news search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 검색 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/company/simple/analyze",
    response_model=NewsAnalysisResponse,
    summary="간소화된 회사 뉴스 검색 및 분석",
    description="""
    회사명만 입력하면 최적화된 설정으로 뉴스를 검색하고 ESG 분석을 수행합니다.
    
    **최적화된 고정 설정:**
    - 검색 결과: 100개
    - 정렬: 정확도 순 (관련성 높은 뉴스 우선)
    - 검색 시작 위치: 1 (가장 관련성 높은 뉴스부터)
    - 중복 제거: 활성화
    - 유사도 임계값: 0.75
    
    **분석 내용:**
    - ESG 카테고리 분류 (Environmental, Social, Governance)
    - 감정 분석 (긍정/부정/중립)
    - 키워드 추출
    
    **사용 예시:**
    ```json
    {
        "company": "삼성전자"
    }
    ```
    """,
    responses={
        200: {"description": "뉴스 검색 및 분석 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"}
    }
)
async def analyze_company_news_simple(
    request: SimpleCompanySearchRequest,
    background_tasks: BackgroundTasks,
    controller: NewsController = Depends(get_news_controller)
):
    """
    간소화된 회사별 뉴스 검색 및 분석 - 회사명만 입력하면 최적화된 설정으로 검색하고 분석
    
    Args:
        request: 간소화된 검색 요청 (회사명만 포함)
        background_tasks: 백그라운드 작업
        controller: 뉴스 컨트롤러
        
    Returns:
        NewsAnalysisResponse: 뉴스 검색 및 분석 결과
    """
    try:
        # 최적화된 검색 요청으로 변환
        optimized_request = request.to_optimized_news_search_request()
        
        # 백그라운드에서 분석 로그 기록
        background_tasks.add_task(
            _log_search_request, 
            "simple_company_analysis", 
            request.company,
            optimized_request.dict()
        )
        
        # 뉴스 검색 및 분석 실행
        return await controller.analyze_company_news(optimized_request)
        
    except Exception as e:
        logger.error(f"Simple company news analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 분석 중 오류가 발생했습니다: {str(e)}")

# === 기존 엔드포인트들 (고급 사용자용) ===

@router.post(
    "/search", 
    response_model=NewsSearchResponse,
    summary="뉴스 검색",
    description="네이버 뉴스 API를 통해 뉴스를 검색합니다. 중복 제거 및 유사도 필터링 기능을 제공합니다.",
    responses={
        200: {"description": "뉴스 검색 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"}
    }
)
async def search_news(
    request: NewsSearchRequest,
    background_tasks: BackgroundTasks,
    controller: NewsController = Depends(get_news_controller)
):
    """
    뉴스 검색 API
    
    Args:
        request: 뉴스 검색 요청
        background_tasks: 백그라운드 작업
        controller: 뉴스 컨트롤러
        
    Returns:
        NewsSearchResponse: 뉴스 검색 결과
    """
    try:
        background_tasks.add_task(_log_search_request, "news_search", request.query, request.dict())
        return await controller.search_news(request)
    except Exception as e:
        logger.error(f"News search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 검색 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/company",
    response_model=NewsSearchResponse,
    summary="회사별 뉴스 검색 (고급)",
    description="""
    회사별 뉴스를 상세 옵션과 함께 검색합니다.
    
    **고급 사용자를 위한 모든 옵션 제공:**
    - 검색 결과 개수 조정 (1~100)
    - 정렬 방식 선택 (정확도순/날짜순)
    - 검색 시작 위치 조정
    - 중복 제거 여부 선택
    - 유사도 임계값 조정
    
    간단한 검색을 원한다면 `/company/simple` 엔드포인트를 사용하세요.
    """,
    responses={
        200: {"description": "뉴스 검색 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"}
    }
)
async def search_company_news(
    request: CompanyNewsRequest,
    background_tasks: BackgroundTasks,
    controller: NewsController = Depends(get_news_controller)
):
    """
    회사별 뉴스 검색 (고급) - 상세 옵션과 함께 회사 뉴스 검색
    
    Args:
        request: 회사별 뉴스 검색 요청
        background_tasks: 백그라운드 작업
        controller: 뉴스 컨트롤러
        
    Returns:
        NewsSearchResponse: 뉴스 검색 결과
    """
    try:
        background_tasks.add_task(_log_search_request, "company_search", request.company, request.dict())
        return await controller.search_company_news(request)
    except Exception as e:
        logger.error(f"Company news search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 뉴스 검색 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/analyze-company",
    response_model=NewsAnalysisResponse,
    summary="회사별 뉴스 분석 (고급)",
    description="""
    회사별 뉴스를 검색하고 ESG 관점에서 분석합니다.
    
    **고급 사용자를 위한 모든 옵션 제공:**
    - 검색 결과 개수 조정 (1~100)
    - 정렬 방식 선택 (정확도순/날짜순)
    - 검색 시작 위치 조정
    - 중복 제거 여부 선택
    - 유사도 임계값 조정
    
    간단한 분석을 원한다면 `/company/simple/analyze` 엔드포인트를 사용하세요.
    """,
    responses={
        200: {"description": "뉴스 분석 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"}
    }
)
async def analyze_company_news(
    request: CompanyNewsRequest,
    background_tasks: BackgroundTasks,
    controller: NewsController = Depends(get_news_controller)
):
    """
    회사별 뉴스 분석 (고급) - 상세 옵션과 함께 회사 뉴스를 검색하고 분석
    
    Args:
        request: 회사별 뉴스 검색 요청
        background_tasks: 백그라운드 작업
        controller: 뉴스 컨트롤러
        
    Returns:
        NewsAnalysisResponse: 뉴스 검색 및 분석 결과
    """
    try:
        # CompanyNewsRequest를 NewsSearchRequest로 변환
        search_request = request.to_news_search_request()
        
        background_tasks.add_task(_log_search_request, "company_analysis", request.company, request.dict())
        return await controller.analyze_company_news(search_request)
    except Exception as e:
        logger.error(f"Company news analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"회사 뉴스 분석 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/search/batch",
    response_model=List[NewsSearchResponse],
    summary="배치 뉴스 검색",
    description="여러 검색 요청을 동시에 처리합니다. 최대 10개까지 동시 처리 가능합니다.",
    responses={
        200: {"description": "배치 검색 성공"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"}
    }
)
async def batch_search_news(
    requests: List[NewsSearchRequest],
    background_tasks: BackgroundTasks,
    controller: NewsController = Depends(get_news_controller)
):
    """
    배치 뉴스 검색 - 여러 검색 요청을 동시에 처리
    
    Args:
        requests: 뉴스 검색 요청 목록 (최대 10개)
        background_tasks: 백그라운드 작업
        controller: 뉴스 컨트롤러
        
    Returns:
        List[NewsSearchResponse]: 뉴스 검색 결과 목록
    """
    try:
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="최대 10개의 요청만 동시에 처리할 수 있습니다.")
        
        queries = [req.query for req in requests]
        background_tasks.add_task(_log_batch_request, "batch_search", queries)
        
        return await controller.batch_search_news(requests)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch news search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"배치 뉴스 검색 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/trending",
    response_model=TrendingKeywordsResponse,
    summary="트렌딩 키워드 조회",
    description="현재 트렌딩 중인 뉴스 키워드를 조회합니다.",
    responses={
        200: {"description": "트렌딩 키워드 조회 성공"},
        500: {"model": ErrorResponse, "description": "서버 오류"}
    }
)
async def get_trending_keywords(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    controller: NewsController = Depends(get_news_controller)
):
    """
    트렌딩 키워드 조회 - 현재 인기 있는 뉴스 키워드 반환
    
    Args:
        category: 카테고리 필터 (선택사항)
        controller: 뉴스 컨트롤러
        
    Returns:
        TrendingKeywordsResponse: 트렌딩 키워드 목록
    """
    try:
        return await controller.get_trending_keywords(category)
    except Exception as e:
        logger.error(f"Trending keywords fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"트렌딩 키워드 조회 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/health",
    summary="헬스체크",
    description="뉴스 서비스의 상태를 확인합니다."
)
async def health_check():
    """뉴스 서비스 헬스체크"""
    return {"status": "healthy", "service": "news-service"}

# === 유틸리티 함수 ===

async def _log_search_request(request_type: str, query: str, request_data: dict):
    """검색 요청 로깅"""
    logger.info(f"Search request - Type: {request_type}, Query: {query}, Data: {request_data}")

async def _log_batch_request(request_type: str, queries: List[str]):
    """배치 요청 로깅"""
    logger.info(f"Batch request - Type: {request_type}, Queries: {queries}") 