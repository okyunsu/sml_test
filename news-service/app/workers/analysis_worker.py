import asyncio
from datetime import datetime
from typing import List
from celery import current_task
from .celery_app import celery_app
from ..core.redis_client import redis_client
from ..domain.controller.news_controller import NewsController
from ..domain.model.news_dto import SimpleCompanySearchRequest
import logging

logger = logging.getLogger(__name__)


@celery_app.task
def test_celery_worker():
    """Celery Worker 테스트용 간단한 작업"""
    try:
        logger.info("Celery Worker 테스트 작업 시작")
        
        # 간단한 Redis 연결 테스트
        redis_client.set_json("test:celery", {"status": "working", "timestamp": datetime.now().isoformat()}, expire=300)
        
        logger.info("Celery Worker 테스트 작업 완료")
        return {"status": "success", "message": "Celery Worker is working!", "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Celery Worker 테스트 실패: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True)
def analyze_companies_periodic(self, companies: List[str]):
    """
    주기적으로 회사들의 뉴스를 분석하는 작업
    
    Args:
        companies: 분석할 회사 목록 (예: ["삼성전자", "LG전자"])
    """
    try:
        logger.info(f"주기적 뉴스 분석 시작: {companies}")
        
        # 비동기 함수를 동기 환경에서 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_analyze_companies_async(companies))
            logger.info(f"주기적 뉴스 분석 완료: {len(result)}개 회사 처리")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"주기적 뉴스 분석 실패: {str(e)}")
        # Celery에서 재시도를 위해 예외를 다시 발생
        self.retry(exc=e, countdown=300, max_retries=3)  # 5분 후 재시도, 최대 3번


async def _analyze_companies_async(companies: List[str]) -> dict:
    """비동기로 회사들의 뉴스를 분석"""
    
    results = {}
    controller = NewsController()
    
    for company in companies:
        try:
            logger.info(f"{company} 뉴스 분석 시작")
            
            # 간소화된 뉴스 분석 요청 생성
            request = SimpleCompanySearchRequest(company=company)
            
            # 뉴스 분석 실행 (기존 API와 동일한 로직 사용)
            analysis_result = await controller.analyze_company_news(
                request.to_optimized_news_search_request()
            )
            
            # 분석 결과를 딕셔너리로 변환
            result_dict = analysis_result.dict() if hasattr(analysis_result, 'dict') else analysis_result
            
            # Redis에 캐시 저장
            cache_key = f"analysis:{company}:latest"
            cache_data = {
                "company": company,
                "analysis_result": result_dict,
                "analyzed_at": datetime.now().isoformat(),
                "cache_key": cache_key
            }
            
            # 24시간 캐시 (86400초)
            redis_client.set_json(cache_key, cache_data, expire=86400)
            
            # 분석 히스토리에도 저장
            history_key = f"analysis:{company}:history"
            history_data = redis_client.get_json(history_key) or []
            
            # 최신 분석 결과를 히스토리 앞쪽에 추가
            history_data.insert(0, cache_data)
            
            # 최대 50개까지만 보관
            if len(history_data) > 50:
                history_data = history_data[:50]
            
            # 히스토리 저장 (7일간 보관)
            redis_client.set_json(history_key, history_data, expire=604800)
            
            results[company] = {
                "status": "success",
                "analyzed_at": cache_data["analyzed_at"],
                "news_count": len(result_dict.get("analyzed_news", [])),
                "cache_key": cache_key
            }
            
            logger.info(f"{company} 뉴스 분석 완료 - {results[company]['news_count']}개 뉴스")
            
        except Exception as e:
            logger.error(f"{company} 뉴스 분석 실패: {str(e)}")
            results[company] = {
                "status": "error",
                "error": str(e),
                "analyzed_at": datetime.now().isoformat()
            }
    
    # 전체 분석 상태 업데이트
    status_data = {
        "last_analysis_at": datetime.now().isoformat(),
        "companies_analyzed": list(companies),
        "results": results,
        "total_success": len([r for r in results.values() if r["status"] == "success"]),
        "total_error": len([r for r in results.values() if r["status"] == "error"])
    }
    
    redis_client.set_json("analysis:status:latest", status_data, expire=86400)
    
    return results


@celery_app.task
def analyze_single_company(company: str):
    """
    단일 회사 뉴스 분석 (수동 트리거용)
    
    Args:
        company: 분석할 회사명
    """
    try:
        logger.info(f"단일 회사 뉴스 분석 시작: {company}")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_analyze_companies_async([company]))
            logger.info(f"단일 회사 뉴스 분석 완료: {company}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"단일 회사 뉴스 분석 실패: {str(e)}")
        raise


@celery_app.task
def clear_old_cache():
    """오래된 캐시 데이터 정리"""
    try:
        logger.info("오래된 캐시 데이터 정리 시작")
        
        # 1주일 이상된 히스토리 키들 찾기
        pattern = "analysis:*:history"
        keys = redis_client.get_all_keys(pattern)
        
        cleaned_count = 0
        for key in keys:
            history_data = redis_client.get_json(key) or []
            if len(history_data) > 100:  # 100개 초과시 50개만 유지
                redis_client.set_json(key, history_data[:50], expire=604800)
                cleaned_count += 1
        
        logger.info(f"캐시 데이터 정리 완료: {cleaned_count}개 키 정리")
        return {"cleaned_keys": cleaned_count}
        
    except Exception as e:
        logger.error(f"캐시 데이터 정리 실패: {str(e)}")
        raise 