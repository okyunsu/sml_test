from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging

from app.domain.controller.gri_controller import GRIController
from app.domain.model.tuning_request import TuningRequest, TaskType
from app.domain.service.tuning_service import TuningService
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gri", tags=["GRI Standards"])

gri_controller = GRIController()
tuning_service = TuningService()

@router.post("/start-gri-standards-tuning")
async def start_gri_standards_tuning(
    background_tasks: BackgroundTasks,
    model_name: str = "klue/bert-base",
    model_type: str = "bert",
    learning_rate: float = 2e-5,
    batch_size: int = 8,
    num_epochs: int = 3,
    use_lora: bool = True
) -> Dict[str, Any]:
    """GRI 기준 자체를 학습하는 파인튜닝 시작 (1단계: GRI 표준 학습)"""
    try:
        logger.info("🚀 GRI 기준 학습 파인튜닝 시작")
        
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        
        # GRI PDF 파일들이 있는 경로 설정 (로컬 환경)
        gri_dataset_path = "data/gri"
        
        # 튜닝 요청 생성
        tuning_request = TuningRequest(
            model_name=model_name,
            model_type=model_type,
            task_type=TaskType.TEXT_GENERATION,  # GRI 기준 설명 생성
            reports_folder=gri_dataset_path,
            base_model_path=None,
            is_continual_learning=False,
            learning_rate=learning_rate,
            batch_size=batch_size,
            num_epochs=num_epochs,
            max_length=1024,  # GRI 기준 설명이 길 수 있으므로
            warmup_steps=500,
            use_lora=use_lora,
            lora_r=16,
            lora_alpha=32,
            lora_dropout=0.1,
            save_steps=500,
            eval_steps=500,
            output_dir=None,
            wandb_project=None
        )
        
        # 백그라운드에서 파인튜닝 실행
        background_tasks.add_task(
            tuning_service.run_fine_tuning,
            job_id,
            tuning_request
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"GRI 기준 학습이 시작되었습니다. (36개 GRI PDF 파일)",
            "status_url": f"/api/v1/tuning/status/{job_id}",
            "tuning_config": {
                "model_name": model_name,
                "task_type": "gri_standards_learning",
                "learning_rate": learning_rate,
                "batch_size": batch_size,
                "num_epochs": num_epochs,
                "use_lora": use_lora
            }
        }
        
    except Exception as e:
        logger.error(f"❌ GRI 기준 학습 시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_gri_models() -> Dict[str, Any]:
    """GRI 학습 모델 목록 조회"""
    try:
        logger.info("📋 GRI 학습 모델 목록 조회")
        result = await gri_controller.list_gri_models()
        return result
    except Exception as e:
        logger.error(f"❌ GRI 모델 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

 