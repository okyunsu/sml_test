import asyncio
from fastapi import HTTPException, status
from app.domain.model.news_dto import (
    NewsSearchRequest, NewsSearchResponse, CompanyNewsRequest,
    TrendingKeywordsResponse, NewsAnalysisResponse
)
from app.domain.service.news_service import NewsService, NewsServiceError, NewsAPIError
from app.domain.service.news_analysis_service import NewsAnalysisService

class NewsController:
    """뉴스 컨트롤러 - 비동기 최적화된 서비스 오케스트레이션 및 HTTP 예외 변환"""
    
    def __init__(self):
        self.news_service = NewsService()
        self.analysis_service = NewsAnalysisService()
    
    async def search_news(self, request: NewsSearchRequest) -> NewsSearchResponse:
        """뉴스 검색 처리 - 비동기 최적화"""
        try:
            return await self.news_service.search_news(request)
        except NewsAPIError as e:
            self._raise_http_exception_from_api_error(e)
            raise  # 타입 체커를 위한 명시적 raise
        except NewsServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"예상치 못한 오류가 발생했습니다: {str(e)}"
            )
    
    async def search_company_news(self, request: CompanyNewsRequest) -> NewsSearchResponse:
        """회사별 뉴스 검색 처리 - 비동기 최적화"""
        try:
            # CompanyNewsRequest를 NewsSearchRequest로 변환
            search_request = request.to_news_search_request()
            return await self.news_service.search_news(search_request)
        except NewsAPIError as e:
            self._raise_http_exception_from_api_error(e)
            raise  # 타입 체커를 위한 명시적 raise
        except NewsServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회사 뉴스 검색 중 예상치 못한 오류가 발생했습니다: {str(e)}"
            )
    
    async def analyze_company_news(self, request: NewsSearchRequest) -> NewsAnalysisResponse:
        """회사 뉴스 분석 처리 - 비동기 최적화 및 동시성 개선"""
        try:
            # 1. 뉴스 검색
            news_response = await self.news_service.search_news(request)
            
            # 2. 회사명 추출 (검색어에서 따옴표 제거)
            company_name = request.query.strip('"')
            
            # 3. 뉴스 분석 (검색 결과가 있을 때만)
            if not news_response.items:
                # 빈 결과에 대한 빠른 응답
                return await self.analysis_service.analyze_company_news(
                    company=company_name,
                    news_response=news_response
                )
            
            # 4. 분석 실행
            return await self.analysis_service.analyze_company_news(
                company=company_name,
                news_response=news_response
            )
            
        except NewsAPIError as e:
            self._raise_http_exception_from_api_error(e)
            raise  # 타입 체커를 위한 명시적 raise
        except NewsServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="뉴스 분석 요청이 시간 초과되었습니다. 잠시 후 다시 시도해주세요."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"뉴스 분석 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_trending_keywords(self, category: str | None = None) -> TrendingKeywordsResponse:
        """트렌딩 키워드 조회 처리 - 비동기 최적화"""
        try:
            return await self.news_service.get_trending_keywords()
        except NewsServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"트렌딩 키워드 조회 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def batch_search_news(self, requests: list[NewsSearchRequest]) -> list[NewsSearchResponse]:
        """배치 뉴스 검색 - 동시성 최적화"""
        if not requests:
            return []
        
        try:
            # 모든 검색 요청을 동시에 처리
            tasks = [
                asyncio.create_task(self.news_service.search_news(request))
                for request in requests
            ]
            
            # 부분 실패를 허용하면서 결과 수집
            results = []
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(completed_tasks):
                if isinstance(result, Exception):
                    # 개별 요청 실패 시 에러 응답 생성
                    error_response = self._create_error_response(requests[i], result)
                    results.append(error_response)
                else:
                    results.append(result)
            
            return results
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"배치 뉴스 검색 중 오류가 발생했습니다: {str(e)}"
            )
    
    def _create_error_response(self, request: NewsSearchRequest, error: Exception) -> NewsSearchResponse:
        """에러 발생 시 기본 응답 생성"""
        return NewsSearchResponse(
            last_build_date="",
            total=0,
            start=request.start,
            display=request.display,
            items=[],
            original_count=0,
            duplicates_removed=0,
            deduplication_enabled=request.remove_duplicates
        )
    
    def _raise_http_exception_from_api_error(self, error: NewsAPIError) -> None:
        """NewsAPIError를 적절한 HTTPException으로 변환"""
        status_code_mapping = {
            400: status.HTTP_400_BAD_REQUEST,
            401: status.HTTP_401_UNAUTHORIZED,
            429: status.HTTP_429_TOO_MANY_REQUESTS,
        }
        
        http_status = status_code_mapping.get(
            error.status_code or 500, 
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        raise HTTPException(status_code=http_status, detail=str(error)) 