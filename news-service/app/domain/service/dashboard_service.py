"""대시보드 도메인 서비스"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from app.config.ml_settings import dashboard_settings
from app.core.redis_client import redis_client
from app.domain.model.news_dto import SimpleCompanySearchRequest

logger = logging.getLogger(__name__)


class DashboardService:
    """대시보드 관련 비즈니스 로직 처리"""
    
    def __init__(self):
        self.settings = dashboard_settings
        self.redis_client = redis_client
    
    async def get_dashboard_status(self) -> Dict[str, Any]:
        """대시보드 전체 상태 조회"""
        try:
            # Redis 연결 상태 확인
            redis_connected = await self._check_redis_connection()
            
            # 전체 분석 상태 조회
            status_data = self.redis_client.get_json("analysis:status:latest")
            
            if not status_data:
                return {
                    "status": "no_data",
                    "message": "아직 분석된 데이터가 없습니다.",
                    "redis_connected": redis_connected,
                    "monitored_companies": self.settings.monitored_companies,
                    "last_analysis_at": None
                }
            
            return {
                "status": "running",
                "redis_connected": redis_connected,
                "monitored_companies": self.settings.monitored_companies,
                "last_analysis_at": status_data.get("last_analysis_at"),
                "analysis_results": status_data.get("results", {}),
                "total_success": status_data.get("total_success", 0),
                "total_error": status_data.get("total_error", 0)
            }
            
        except Exception as e:
            logger.error(f"대시보드 상태 조회 실패: {str(e)}")
            raise DashboardServiceError(f"상태 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def _check_redis_connection(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            test_key = "test:connection"
            self.redis_client.set_json(test_key, {"test": "connection"}, expire=1)
            test_result = self.redis_client.get_json(test_key)
            return test_result is not None
        except Exception as e:
            logger.error(f"Redis 연결 상태 확인 실패: {str(e)}")
            return False
    
    async def get_monitored_companies(self) -> Dict[str, Any]:
        """모니터링 중인 회사 목록 조회"""
        return {
            "companies": self.settings.monitored_companies,
            "total_count": len(self.settings.monitored_companies),
            "analysis_interval": f"{self.settings.analysis_interval_minutes}분마다"
        }
    
    async def get_company_analysis(self, company: str) -> Dict[str, Any]:
        """특정 회사의 최신 분석 결과 조회"""
        try:
            if company not in self.settings.monitored_companies:
                raise CompanyNotMonitoredError(
                    f"모니터링 중이지 않은 회사입니다. 가능한 회사: {self.settings.monitored_companies}"
                )
            
            cache_key = f"analysis:{company}:latest"
            analysis_data = self.redis_client.get_json(cache_key)
            
            if not analysis_data:
                return {
                    "company": company,
                    "status": "no_data",
                    "message": f"{company}의 분석 데이터가 없습니다. 첫 번째 분석을 기다리거나 수동 분석을 요청하세요.",
                    "analyzed_at": None
                }
            
            return {
                "company": company,
                "status": "success",
                "analyzed_at": analysis_data.get("analyzed_at"),
                "analysis_result": analysis_data.get("analysis_result"),
                "cache_key": analysis_data.get("cache_key")
            }
            
        except CompanyNotMonitoredError:
            raise
        except Exception as e:
            logger.error(f"{company} 분석 결과 조회 실패: {str(e)}")
            raise DashboardServiceError(f"분석 결과 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def get_company_analysis_history(self, company: str, limit: int = 20) -> Dict[str, Any]:
        """특정 회사의 분석 히스토리 조회"""
        try:
            if company not in self.settings.monitored_companies:
                raise CompanyNotMonitoredError(
                    f"모니터링 중이지 않은 회사입니다. 가능한 회사: {self.settings.monitored_companies}"
                )
            
            history_key = f"analysis:{company}:history"
            history_data = self.redis_client.get_json(history_key) or []
            
            # 제한된 개수만 반환
            limited_history = history_data[:limit]
            
            return {
                "company": company,
                "total_count": len(history_data),
                "returned_count": len(limited_history),
                "history": limited_history
            }
            
        except CompanyNotMonitoredError:
            raise
        except Exception as e:
            logger.error(f"{company} 분석 히스토리 조회 실패: {str(e)}")
            raise DashboardServiceError(f"분석 히스토리 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def get_all_latest_analysis(self) -> Dict[str, Any]:
        """모든 회사의 최신 분석 결과 조회"""
        try:
            results = {}
            
            for company in self.settings.monitored_companies:
                cache_key = f"analysis:{company}:latest"
                analysis_data = self.redis_client.get_json(cache_key)
                
                if analysis_data:
                    results[company] = {
                        "status": "success",
                        "analyzed_at": analysis_data.get("analyzed_at"),
                        "analysis_result": analysis_data.get("analysis_result"),
                        "cache_key": analysis_data.get("cache_key")
                    }
                else:
                    results[company] = {
                        "status": "no_data",
                        "message": f"{company}의 분석 데이터가 없습니다.",
                        "analyzed_at": None
                    }
            
            return {
                "companies": self.settings.monitored_companies,
                "results": results,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"전체 분석 결과 조회 실패: {str(e)}")
            raise DashboardServiceError(f"전체 분석 결과 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def request_company_analysis(self, company: str) -> Dict[str, Any]:
        """특정 회사의 수동 분석 요청"""
        try:
            if company not in self.settings.monitored_companies:
                raise CompanyNotMonitoredError(
                    f"모니터링 중이지 않은 회사입니다. 가능한 회사: {self.settings.monitored_companies}"
                )
            
            # 분석 작업을 Celery 큐에 추가
            from app.workers.analysis_worker import analyze_single_company
            task = analyze_single_company.delay(company)
            
            return {
                "company": company,
                "status": "requested",
                "message": f"{company} 뉴스 분석을 백그라운드에서 시작했습니다.",
                "task_id": task.id,
                "estimated_completion": "약 2-5분 후 완료 예정"
            }
            
        except CompanyNotMonitoredError:
            raise
        except Exception as e:
            logger.error(f"{company} 수동 분석 요청 실패: {str(e)}")
            raise DashboardServiceError(f"분석 요청 중 오류가 발생했습니다: {str(e)}")
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """캐시 정보 조회"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            
            cache_info = {}
            for company in self.settings.monitored_companies:
                latest_key = f"analysis:{company}:latest"
                history_key = f"analysis:{company}:history"
                
                latest_data = self.redis_client.get_json(latest_key)
                history_data = self.redis_client.get_json(history_key) or []
                
                cache_info[company] = {
                    "latest_exists": latest_data is not None,
                    "latest_key": latest_key,
                    "history_count": len(history_data),
                    "history_key": history_key,
                    "last_updated": latest_data.get("analyzed_at") if latest_data else None
                }
            
            # 전체 상태 정보
            status_data = self.redis_client.get_json("analysis:status:latest")
            
            return {
                "companies": cache_info,
                "global_status": {
                    "exists": status_data is not None,
                    "last_analysis": status_data.get("last_analysis_at") if status_data else None
                },
                "cache_settings": {
                    "cache_expire_hours": self.settings.cache_expire_hours,
                    "history_max_count": self.settings.history_max_count,
                    "history_expire_days": self.settings.history_expire_days
                }
            }
            
        except Exception as e:
            logger.error(f"캐시 정보 조회 실패: {str(e)}")
            raise DashboardServiceError(f"캐시 정보 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def clear_company_cache(self, company: str) -> Dict[str, Any]:
        """특정 회사의 캐시 삭제"""
        try:
            if company not in self.settings.monitored_companies:
                raise CompanyNotMonitoredError(
                    f"모니터링 중이지 않은 회사입니다. 가능한 회사: {self.settings.monitored_companies}"
                )
            
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            
            latest_key = f"analysis:{company}:latest"
            history_key = f"analysis:{company}:history"
            
            # 캐시 삭제
            deleted_keys = []
            if self.redis_client.get_json(latest_key):
                self.redis_client.delete(latest_key)
                deleted_keys.append(latest_key)
            
            if self.redis_client.get_json(history_key):
                self.redis_client.delete(history_key)
                deleted_keys.append(history_key)
            
            return {
                "company": company,
                "status": "cleared",
                "deleted_keys": deleted_keys,
                "message": f"{company}의 캐시 데이터를 삭제했습니다."
            }
            
        except CompanyNotMonitoredError:
            raise
        except Exception as e:
            logger.error(f"{company} 캐시 삭제 실패: {str(e)}")
            raise DashboardServiceError(f"캐시 삭제 중 오류가 발생했습니다: {str(e)}")
    
    async def test_celery_connection(self) -> Dict[str, Any]:
        """Celery Worker 연결 테스트"""
        try:
            from app.workers.analysis_worker import test_celery_worker
            task = test_celery_worker.delay()
            
            return {
                "status": "requested",
                "message": "Celery Worker 테스트 작업을 시작했습니다.",
                "task_id": task.id,
                "test_instruction": "5초 후 /api/v1/dashboard/test/result 엔드포인트로 결과를 확인하세요."
            }
            
        except Exception as e:
            logger.error(f"Celery 테스트 실패: {str(e)}")
            raise DashboardServiceError(f"Celery 테스트 중 오류가 발생했습니다: {str(e)}")
    
    async def get_cache_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """범용 캐시 데이터 조회"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            cached_data = self.redis_client.get_json(cache_key)
            return cached_data
        except Exception as e:
            logger.error(f"캐시 조회 실패 ({cache_key}): {str(e)}")
            return None
    
    async def set_cache_data(self, cache_key: str, data: Dict[str, Any], expire_minutes: int = 30) -> bool:
        """범용 캐시 데이터 저장"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            self.redis_client.set_json(cache_key, data, expire=expire_minutes * 60)
            logger.info(f"캐시 저장 완료 ({cache_key}), 만료: {expire_minutes}분")
            return True
        except Exception as e:
            logger.error(f"캐시 저장 실패 ({cache_key}): {str(e)}")
            return False

    async def get_test_result(self) -> Dict[str, Any]:
        """Celery 테스트 결과 확인"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            
            test_data = self.redis_client.get_json("test:celery")
            
            if not test_data:
                return {
                    "status": "no_result",
                    "message": "테스트 결과가 없습니다. 먼저 테스트를 실행하세요."
                }
            
            return {
                "status": "success",
                "test_result": test_data,
                "message": "Celery Worker가 정상적으로 작동하고 있습니다!"
            }
            
        except Exception as e:
            logger.error(f"테스트 결과 조회 실패: {str(e)}")
            raise DashboardServiceError(f"테스트 결과 조회 중 오류가 발생했습니다: {str(e)}")


class DashboardServiceError(Exception):
    """대시보드 서비스 도메인 예외"""
    pass


class CompanyNotMonitoredError(DashboardServiceError):
    """모니터링하지 않는 회사 예외"""
    pass 