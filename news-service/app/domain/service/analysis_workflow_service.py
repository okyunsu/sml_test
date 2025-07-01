"""분석 워크플로우 서비스 - Worker 전용"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import logging

from app.domain.model.news_dto import SimpleCompanySearchRequest
from app.domain.service.news_service import NewsService
from app.domain.service.news_analysis_service import NewsAnalysisService
from app.core.redis_client import redis_client
from app.config.ml_settings import dashboard_settings

logger = logging.getLogger(__name__)


class AnalysisWorkflowService:
    """분석 워크플로우 처리 서비스 - Worker에서 사용"""
    
    def __init__(self):
        self.news_service = NewsService()
        self.analysis_service = NewsAnalysisService()
        self.redis_client = redis_client
        self.settings = dashboard_settings
    
    async def analyze_single_company(self, company: str) -> Dict[str, Any]:
        """단일 회사 뉴스 분석"""
        try:
            logger.info(f"{company} 뉴스 분석 시작")
            
            # 간소화된 뉴스 분석 요청 생성
            request = SimpleCompanySearchRequest(company=company)
            search_request = request.to_optimized_news_search_request()
            
            # 뉴스 검색
            news_response = await self.news_service.search_news(search_request)
            
            # 뉴스 분석
            analysis_result = await self.analysis_service.analyze_company_news(
                company=company,
                news_response=news_response
            )
            
            # 분석 결과를 딕셔너리로 변환
            result_dict = analysis_result.dict() if hasattr(analysis_result, 'dict') else analysis_result
            
            # 캐시 저장
            await self._save_analysis_to_cache(company, result_dict)
            
            logger.info(f"{company} 뉴스 분석 완료")
            
            return {
                "status": "success",
                "company": company,
                "analyzed_at": datetime.now().isoformat(),
                "news_count": len(result_dict.get("analyzed_news", [])),
                "analysis_method": result_dict.get("ml_service_status", "unknown")
            }
            
        except Exception as e:
            logger.error(f"{company} 뉴스 분석 실패: {str(e)}")
            return {
                "status": "error",
                "company": company,
                "error": str(e),
                "analyzed_at": datetime.now().isoformat()
            }
    
    async def analyze_multiple_companies(self, companies: List[str]) -> Dict[str, Any]:
        """여러 회사 뉴스 분석"""
        results = {}
        
        for company in companies:
            try:
                result = await self.analyze_single_company(company)
                results[company] = result
                
            except Exception as e:
                logger.error(f"{company} 분석 중 오류: {str(e)}")
                results[company] = {
                    "status": "error",
                    "company": company,
                    "error": str(e),
                    "analyzed_at": datetime.now().isoformat()
                }
        
        # 전체 분석 상태 업데이트
        await self._update_global_analysis_status(companies, results)
        
        return results
    
    async def _save_analysis_to_cache(self, company: str, result_dict: Dict[str, Any]):
        """분석 결과를 캐시에 저장"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            
            # 최신 결과 캐시 저장
            cache_key = f"analysis:{company}:latest"
            cache_data = {
                "company": company,
                "analysis_result": result_dict,
                "analyzed_at": datetime.now().isoformat(),
                "cache_key": cache_key
            }
            
            # 캐시 만료 시간 (시간 단위)
            expire_seconds = self.settings.cache_expire_hours * 3600
            self.redis_client.set_json(cache_key, cache_data, expire=expire_seconds)
            
            # 분석 히스토리에도 저장
            await self._save_to_history(company, cache_data)
            
        except Exception as e:
            logger.error(f"{company} 캐시 저장 실패: {str(e)}")
    
    async def _save_to_history(self, company: str, cache_data: Dict[str, Any]):
        """분석 히스토리에 저장"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            
            history_key = f"analysis:{company}:history"
            history_data = self.redis_client.get_json(history_key) or []
            
            # 최신 분석 결과를 히스토리 앞쪽에 추가
            history_data.insert(0, cache_data)
            
            # 최대 개수 제한
            if len(history_data) > self.settings.history_max_count:
                history_data = history_data[:self.settings.history_max_count]
            
            # 히스토리 저장 (일 단위)
            expire_seconds = self.settings.history_expire_days * 24 * 3600
            self.redis_client.set_json(history_key, history_data, expire=expire_seconds)
            
        except Exception as e:
            logger.error(f"{company} 히스토리 저장 실패: {str(e)}")
    
    async def _update_global_analysis_status(self, companies: List[str], results: Dict[str, Any]):
        """전체 분석 상태 업데이트"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            
            status_data = {
                "last_analysis_at": datetime.now().isoformat(),
                "companies_analyzed": list(companies),
                "results": results,
                "total_success": len([r for r in results.values() if r["status"] == "success"]),
                "total_error": len([r for r in results.values() if r["status"] == "error"])
            }
            
            # 24시간 캐시
            self.redis_client.set_json("analysis:status:latest", status_data, expire=86400)
            
        except Exception as e:
            logger.error(f"전체 분석 상태 업데이트 실패: {str(e)}")
    
    async def clear_old_cache(self) -> Dict[str, Any]:
        """오래된 캐시 데이터 정리"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            
            logger.info("오래된 캐시 데이터 정리 시작")
            
            cleaned_count = 0
            
            # 각 회사의 히스토리 데이터 정리
            for company in self.settings.monitored_companies:
                history_key = f"analysis:{company}:history"
                history_data = self.redis_client.get_json(history_key) or []
                
                if len(history_data) > self.settings.history_max_count:
                    # 최대 개수만 유지
                    cleaned_data = history_data[:self.settings.history_max_count]
                    expire_seconds = self.settings.history_expire_days * 24 * 3600
                    self.redis_client.set_json(history_key, cleaned_data, expire=expire_seconds)
                    cleaned_count += 1
            
            logger.info(f"캐시 데이터 정리 완료: {cleaned_count}개 키 정리")
            
            return {
                "status": "success",
                "cleaned_keys": cleaned_count,
                "cleaned_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"캐시 데이터 정리 실패: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "cleaned_at": datetime.now().isoformat()
            }
    
    async def test_redis_connection(self) -> Dict[str, Any]:
        """Redis 연결 테스트"""
        try:
            await asyncio.sleep(0)  # 비동기 처리를 위한 양보
            
            test_key = "test:celery"
            test_data = {
                "status": "working", 
                "timestamp": datetime.now().isoformat(),
                "message": "Celery Worker is working!"
            }
            
            # 5분간 테스트 데이터 저장
            self.redis_client.set_json(test_key, test_data, expire=300)
            
            return test_data
            
        except Exception as e:
            logger.error(f"Redis 연결 테스트 실패: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 