from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Optional
from app.domain.controller.tuning_controller import TuningController
from app.domain.model.tuning_request import TuningRequest, InferenceRequest
from app.domain.model.tuning_response import TuningResponse, InferenceResponse, TuningStatus
from app.config.gpu_config import monitor_gpu_memory, cleanup_gpu_memory
import logging
import os

router = APIRouter(prefix="/api/v1/tuning", tags=["ESG Fine-tuning"])

tuning_controller = TuningController()
logger = logging.getLogger(__name__)

def _set_default_reports_folder(request: TuningRequest) -> None:
    """공통 폴더 경로 설정 로직"""
    if not request.reports_folder or request.reports_folder == "/app/data/uploads":
        # 로컬 환경과 Docker 환경 구분
        if os.path.exists("/app"):
            request.reports_folder = "/app/data/uploads"
        else:
            request.reports_folder = "data/uploads"

# ============================================================================
# 🎯 핵심 튜닝 기능
# ============================================================================

@router.post("/start", response_model=TuningResponse)
async def start_fine_tuning(
    background_tasks: BackgroundTasks,
    request: TuningRequest
):
    """ESG 보고서 기반 파인튜닝 시작"""
    try:
        _set_default_reports_folder(request)
        return await tuning_controller.start_fine_tuning(background_tasks, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/continue", response_model=TuningResponse)
async def continue_fine_tuning(
    background_tasks: BackgroundTasks,
    request: TuningRequest
):
    """기존 모델을 기반으로 지속가능경영보고서로 계속 학습 시작"""
    try:
        # 지속가능경영보고서 폴더로 설정
        request.reports_folder = "data/uploads"
        request.is_continual_learning = True
        
        logger.info(f"🔄 계속 학습 시작: {request.base_model_path} → 지속가능경영보고서 학습")
        return await tuning_controller.start_fine_tuning(background_tasks, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=TuningStatus)
async def get_tuning_status(job_id: str):
    """파인튜닝 작업 상태 조회"""
    try:
        return await tuning_controller.get_tuning_status(job_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """파인튜닝된 모델로 추론 수행"""
    try:
        return await tuning_controller.inference(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# 📁 모델 관리
# ============================================================================

@router.get("/models")
async def list_available_models():
    """사용 가능한 파인튜닝된 모델 목록 조회"""
    try:
        return await tuning_controller.list_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """파인튜닝된 모델 삭제"""
    try:
        return await tuning_controller.delete_model(model_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ============================================================================
# 🎮 시스템 모니터링
# ============================================================================

@router.get("/health")
async def health_check():
    """🏥 서비스 상태 확인 (GPU 상태 포함)"""
    try:
        import torch
        from datetime import datetime
        
        # 기본 서비스 상태
        service_status = {
            "service": "ESG Fine-tuning Service",
            "status": "healthy",
            "version": "2.0.0-rtx2080",
            "timestamp": datetime.now().isoformat()
        }
        
        # GPU 상태 통합
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            memory_info = monitor_gpu_memory()
            
            service_status["gpu"] = {
                "available": True,
                "name": gpu_name,
                "memory": memory_info,
                "rtx2080_optimized": "2080" in gpu_name,
                "cuda_version": getattr(torch.version, 'cuda', 'unknown')
            }
        else:
            service_status["gpu"] = {
                "available": False,
                "message": "CPU 모드로 실행 중"
            }
        
        return service_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 실패: {str(e)}")

@router.post("/gpu/cleanup")
async def cleanup_gpu():
    """🧹 GPU 메모리 정리"""
    try:
        import torch
        
        if not torch.cuda.is_available():
            return {
                "success": False,
                "message": "CUDA를 사용할 수 없습니다"
            }
        
        # 정리 전후 메모리 상태 비교
        before_memory = monitor_gpu_memory()
        cleanup_gpu_memory()
        after_memory = monitor_gpu_memory()
        
        freed_memory = before_memory.get("allocated_gb", 0) - after_memory.get("allocated_gb", 0)
        
        return {
            "success": True,
            "message": "GPU 메모리 정리 완료",
            "freed_memory_gb": round(freed_memory, 2),
            "memory_status": {
                "before": before_memory,
                "after": after_memory
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPU 메모리 정리 실패: {str(e)}") 