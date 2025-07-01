"""대시보드 컨트롤러"""
import asyncio
from fastapi import HTTPException, status
from typing import Dict, Any

from app.domain.service.dashboard_service import (
    DashboardService, DashboardServiceError, CompanyNotMonitoredError
)


class DashboardController:
    """대시보드 컨트롤러 - HTTP 예외 변환 및 서비스 오케스트레이션"""
    
    def __init__(self):
        self.dashboard_service = DashboardService()
    
    async def get_dashboard_status(self) -> Dict[str, Any]:
        """대시보드 전체 상태 조회"""
        try:
            return await self.dashboard_service.get_dashboard_status()
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"예상치 못한 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_monitored_companies(self) -> Dict[str, Any]:
        """모니터링 중인 회사 목록 조회"""
        try:
            return await self.dashboard_service.get_monitored_companies()
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회사 목록 조회 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_company_analysis(self, company: str) -> Dict[str, Any]:
        """특정 회사의 최신 분석 결과 조회"""
        try:
            return await self.dashboard_service.get_company_analysis(company)
        except CompanyNotMonitoredError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"분석 결과 조회 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_company_analysis_history(self, company: str, limit: int = 20) -> Dict[str, Any]:
        """특정 회사의 분석 히스토리 조회"""
        try:
            return await self.dashboard_service.get_company_analysis_history(company, limit)
        except CompanyNotMonitoredError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"분석 히스토리 조회 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_all_latest_analysis(self) -> Dict[str, Any]:
        """모든 회사의 최신 분석 결과 조회"""
        try:
            return await self.dashboard_service.get_all_latest_analysis()
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"전체 분석 결과 조회 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def request_company_analysis(self, company: str) -> Dict[str, Any]:
        """특정 회사의 수동 분석 요청"""
        try:
            return await self.dashboard_service.request_company_analysis(company)
        except CompanyNotMonitoredError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"분석 요청 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """캐시 정보 조회"""
        try:
            return await self.dashboard_service.get_cache_info()
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"캐시 정보 조회 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def clear_company_cache(self, company: str) -> Dict[str, Any]:
        """특정 회사의 캐시 삭제"""
        try:
            return await self.dashboard_service.clear_company_cache(company)
        except CompanyNotMonitoredError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"캐시 삭제 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def test_celery_connection(self) -> Dict[str, Any]:
        """Celery Worker 연결 테스트"""
        try:
            return await self.dashboard_service.test_celery_connection()
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Celery 테스트 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_test_result(self) -> Dict[str, Any]:
        """Celery 테스트 결과 확인"""
        try:
            return await self.dashboard_service.get_test_result()
        except DashboardServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"테스트 결과 조회 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_cache_data(self, cache_key: str):
        """캐시 데이터 조회 (스마트 검색용)"""
        try:
            return await self.dashboard_service.get_cache_data(cache_key)
        except Exception as e:
            # 캐시 조회 실패는 로그만 남기고 None 반환 (폴백 허용)
            return None
    
    async def set_cache_data(self, cache_key: str, data: Dict[str, Any], expire_minutes: int = 30) -> bool:
        """캐시 데이터 저장 (스마트 검색용)"""
        try:
            return await self.dashboard_service.set_cache_data(cache_key, data, expire_minutes)
        except Exception as e:
            # 캐시 저장 실패는 로그만 남기고 False 반환 (서비스 중단 방지)
            return False 