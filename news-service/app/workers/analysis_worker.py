"""분석 워커 - 개선된 비동기 처리"""
import asyncio
import logging
from datetime import datetime
from typing import List
from celery import current_task
from .celery_app import celery_app
from app.core.dependencies import setup_dependencies, get_dependency

logger = logging.getLogger(__name__)

# Worker에서 의존성 주입 설정
setup_dependencies()
container = get_dependency()

def run_async_safely(coro):
    """안전한 비동기 실행 - 기존 이벤트 루프와의 충돌 방지"""
    try:
        # 기존 이벤트 루프가 있는지 확인
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 실행 중인 루프가 있으면 새로운 루프 생성
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            # 루프가 없으면 직접 실행
            return loop.run_until_complete(coro)
    except RuntimeError:
        # 완전히 새로운 루프에서 실행
        return asyncio.run(coro)

@celery_app.task
def test_celery_worker():
    """Celery Worker 테스트용 간단한 작업"""
    try:
        logger.info("Celery Worker 테스트 작업 시작")
        
        async def test_task():
            workflow_service = container.get("analysis_workflow_service")
            return await workflow_service.test_redis_connection()
        
        result = run_async_safely(test_task())
        logger.info("Celery Worker 테스트 작업 완료")
        return result
            
    except Exception as e:
        logger.error(f"Celery Worker 테스트 실패: {str(e)}")
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@celery_app.task(bind=True)
def analyze_companies_periodic(self, companies: List[str]):
    """
    주기적으로 회사들의 뉴스를 분석하는 작업
    
    Args:
        companies: 분석할 회사 목록 (예: ["삼성전자", "LG전자"])
    """
    try:
        logger.info(f"주기적 뉴스 분석 시작: {companies}")
        
        async def analysis_task():
            workflow_service = container.get("analysis_workflow_service")
            return await workflow_service.analyze_multiple_companies(companies)
        
        result = run_async_safely(analysis_task())
        
        success_count = len([r for r in result.values() if r["status"] == "success"])
        logger.info(f"주기적 뉴스 분석 완료: {success_count}/{len(companies)}개 회사 성공")
        
        return result
            
    except Exception as e:
        logger.error(f"주기적 뉴스 분석 실패: {str(e)}")
        # Celery에서 재시도를 위해 예외를 다시 발생
        self.retry(exc=e, countdown=300, max_retries=3)  # 5분 후 재시도, 최대 3번

@celery_app.task
def analyze_single_company(company: str):
    """
    단일 회사 뉴스 분석 (수동 트리거용)
    
    Args:
        company: 분석할 회사명
    """
    try:
        logger.info(f"단일 회사 뉴스 분석 시작: {company}")
        
        async def analysis_task():
            workflow_service = container.get("analysis_workflow_service")
            return await workflow_service.analyze_single_company(company)
        
        result = run_async_safely(analysis_task())
        logger.info(f"단일 회사 뉴스 분석 완료: {company} - {result['status']}")
        return result
            
    except Exception as e:
        logger.error(f"단일 회사 뉴스 분석 실패: {str(e)}")
        raise

@celery_app.task
def clear_old_cache():
    """오래된 캐시 데이터 정리"""
    try:
        logger.info("오래된 캐시 데이터 정리 시작")
        
        async def clear_task():
            workflow_service = container.get("analysis_workflow_service")
            return await workflow_service.clear_old_cache()
        
        result = run_async_safely(clear_task())
        logger.info(f"캐시 데이터 정리 완료: {result['cleaned_keys']}개 키 정리")
        return result
            
    except Exception as e:
        logger.error(f"캐시 데이터 정리 실패: {str(e)}")
        raise

@celery_app.task
def analyze_monitored_companies():
    """
    설정된 모니터링 회사들의 자동 분석
    - 환경변수나 설정 파일에서 회사 목록을 가져와서 분석
    """
    try:
        dashboard_settings = container.get("dashboard_settings")
        companies = dashboard_settings.monitored_companies
        logger.info(f"모니터링 회사 자동 분석 시작: {companies}")
        
        async def analysis_task():
            workflow_service = container.get("analysis_workflow_service")
            return await workflow_service.analyze_multiple_companies(companies)
        
        result = run_async_safely(analysis_task())
        logger.info(f"모니터링 회사 자동 분석 완료")
        return result
        
    except Exception as e:
        logger.error(f"모니터링 회사 자동 분석 실패: {str(e)}")
        raise 