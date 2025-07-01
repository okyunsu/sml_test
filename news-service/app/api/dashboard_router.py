from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from ..core.redis_client import redis_client
from ..workers.analysis_worker import analyze_single_company, test_celery_worker
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 분석 대상 회사 목록 (하드코딩)
MONITORED_COMPANIES = ["삼성전자", "LG전자"]


@router.get(
    "/status",
    summary="대시보드 전체 상태 조회",
    description="현재 대시보드의 전체 상태와 마지막 분석 정보를 조회합니다."
)
async def get_dashboard_status():
    """대시보드 전체 상태 조회"""
    try:
        # Redis 연결 상태 확인 (먼저 실행)
        redis_connected = False
        try:
            # 간단한 Redis 연결 테스트
            test_key = "test:connection"
            redis_client.set_json(test_key, {"test": "connection"}, expire=1)
            test_result = redis_client.get_json(test_key)
            redis_connected = (test_result is not None)
            logger.info(f"Redis 연결 상태: {redis_connected}")
            
        except Exception as e:
            error_msg = f"Redis 연결 상태 확인 실패: {str(e)}"
            logger.error(error_msg)
            redis_connected = False
        
        # 전체 분석 상태 조회
        status_data = redis_client.get_json("analysis:status:latest")
        
        if not status_data:
            return {
                "status": "no_data",
                "message": "아직 분석된 데이터가 없습니다.",
                "redis_connected": redis_connected,
                "monitored_companies": MONITORED_COMPANIES,
                "last_analysis_at": None
            }
        
        return {
            "status": "running",
            "redis_connected": redis_connected,
            "monitored_companies": MONITORED_COMPANIES,
            "last_analysis_at": status_data.get("last_analysis_at"),
            "analysis_results": status_data.get("results", {}),
            "total_success": status_data.get("total_success", 0),
            "total_error": status_data.get("total_error", 0)
        }
        
    except Exception as e:
        logger.error(f"대시보드 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상태 조회 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/companies",
    summary="모니터링 중인 회사 목록",
    description="현재 30분마다 자동 분석 중인 회사 목록을 조회합니다."
)
async def get_monitored_companies():
    """모니터링 중인 회사 목록 조회"""
    return {
        "companies": MONITORED_COMPANIES,
        "total_count": len(MONITORED_COMPANIES),
        "analysis_interval": "30분마다"
    }


@router.get(
    "/analysis/{company}",
    summary="특정 회사 최신 분석 결과",
    description="특정 회사의 가장 최근 분석 결과를 조회합니다."
)
async def get_company_analysis(company: str):
    """특정 회사의 최신 분석 결과 조회"""
    try:
        if company not in MONITORED_COMPANIES:
            raise HTTPException(
                status_code=404, 
                detail=f"모니터링 중이지 않은 회사입니다. 가능한 회사: {MONITORED_COMPANIES}"
            )
        
        cache_key = f"analysis:{company}:latest"
        analysis_data = redis_client.get_json(cache_key)
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{company} 분석 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 결과 조회 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/analysis/{company}/history",
    summary="특정 회사 분석 히스토리",
    description="특정 회사의 과거 분석 이력을 조회합니다."
)
async def get_company_analysis_history(
    company: str,
    limit: int = Query(20, ge=1, le=50, description="조회할 이력 개수")
):
    """특정 회사의 분석 히스토리 조회"""
    try:
        if company not in MONITORED_COMPANIES:
            raise HTTPException(
                status_code=404, 
                detail=f"모니터링 중이지 않은 회사입니다. 가능한 회사: {MONITORED_COMPANIES}"
            )
        
        history_key = f"analysis:{company}:history"
        history_data = redis_client.get_json(history_key) or []
        
        # 제한된 개수만 반환
        limited_history = history_data[:limit]
        
        return {
            "company": company,
            "total_count": len(history_data),
            "returned_count": len(limited_history),
            "history": limited_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{company} 분석 히스토리 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 히스토리 조회 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/latest",
    summary="모든 회사 최신 분석 결과",
    description="모든 모니터링 회사의 최신 분석 결과를 한 번에 조회합니다."
)
async def get_all_latest_analysis():
    """모든 회사의 최신 분석 결과 조회"""
    try:
        results = {}
        
        for company in MONITORED_COMPANIES:
            cache_key = f"analysis:{company}:latest"
            analysis_data = redis_client.get_json(cache_key)
            
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
            "companies": MONITORED_COMPANIES,
            "results": results,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"전체 분석 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"전체 분석 결과 조회 중 오류가 발생했습니다: {str(e)}")


@router.post(
    "/analyze/{company}",
    summary="특정 회사 수동 분석 요청",
    description="특정 회사의 뉴스 분석을 즉시 백그라운드로 요청합니다."
)
async def request_company_analysis(company: str):
    """특정 회사 수동 분석 요청"""
    try:
        if company not in MONITORED_COMPANIES:
            raise HTTPException(
                status_code=404, 
                detail=f"모니터링 중이지 않은 회사입니다. 가능한 회사: {MONITORED_COMPANIES}"
            )
        
        # Celery 작업 큐에 분석 작업 추가
        task = analyze_single_company.delay(company)
        
        return {
            "company": company,
            "status": "requested",
            "message": f"{company} 뉴스 분석이 백그라운드에서 시작되었습니다.",
            "task_id": task.id,
            "requested_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{company} 수동 분석 요청 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 요청 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/cache/info",
    summary="캐시 정보 조회",
    description="현재 Redis에 저장된 캐시 정보를 조회합니다."
)
async def get_cache_info():
    """캐시 정보 조회"""
    try:
        cache_info = {}
        
        for company in MONITORED_COMPANIES:
            latest_key = f"analysis:{company}:latest"
            history_key = f"analysis:{company}:history"
            
            latest_exists = redis_client.exists(latest_key)
            history_data = redis_client.get_json(history_key) or []
            
            cache_info[company] = {
                "latest_cached": latest_exists,
                "history_count": len(history_data),
                "latest_key": latest_key,
                "history_key": history_key
            }
        
        # 전체 캐시 키 개수
        all_keys = redis_client.get_all_keys("analysis:*")
        
        return {
            "companies": cache_info,
            "total_cache_keys": len(all_keys),
            "cache_keys": all_keys,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"캐시 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캐시 정보 조회 중 오류가 발생했습니다: {str(e)}")


@router.delete(
    "/cache/{company}",
    summary="특정 회사 캐시 삭제",
    description="특정 회사의 모든 캐시 데이터를 삭제합니다."
)
async def clear_company_cache(company: str):
    """특정 회사의 캐시 삭제"""
    try:
        if company not in MONITORED_COMPANIES:
            raise HTTPException(
                status_code=404, 
                detail=f"모니터링 중이지 않은 회사입니다. 가능한 회사: {MONITORED_COMPANIES}"
            )
        
        # 해당 회사의 모든 캐시 키 찾기
        pattern = f"analysis:{company}:*"
        keys = redis_client.get_all_keys(pattern)
        
        deleted_count = 0
        for key in keys:
            if redis_client.delete(key):
                deleted_count += 1
        
        return {
            "company": company,
            "status": "success",
            "deleted_keys": deleted_count,
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{company} 캐시 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캐시 삭제 중 오류가 발생했습니다: {str(e)}")


@router.post(
    "/test/celery",
    summary="Celery Worker 테스트",
    description="Celery Worker가 정상 작동하는지 간단한 테스트 작업을 실행합니다."
)
async def test_celery():
    """Celery Worker 테스트"""
    try:
        # 간단한 테스트 작업을 Celery 큐에 추가
        task = test_celery_worker.delay()
        
        return {
            "status": "requested",
            "message": "Celery Worker 테스트 작업이 요청되었습니다.",
            "task_id": task.id,
            "requested_at": datetime.now().isoformat(),
            "instruction": "몇 초 후 GET /api/v1/dashboard/test/result를 호출하여 결과를 확인하세요."
        }
        
    except Exception as e:
        logger.error(f"Celery 테스트 요청 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Celery 테스트 요청 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/test/result",
    summary="Celery 테스트 결과 확인",
    description="테스트 작업 결과를 Redis에서 확인합니다."
)
async def get_test_result():
    """Celery 테스트 결과 확인"""
    try:
        test_result = redis_client.get_json("test:celery")
        
        if not test_result:
            return {
                "status": "no_result",
                "message": "테스트 결과가 없습니다. 테스트를 먼저 실행하거나 잠시 후 다시 시도하세요.",
                "checked_at": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "message": "Celery Worker가 정상 작동하고 있습니다!",
            "test_result": test_result,
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Celery 테스트 결과 확인 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테스트 결과 확인 중 오류가 발생했습니다: {str(e)}") 