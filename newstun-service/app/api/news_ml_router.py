from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.domain.service.news_ml_service import NewsMLService
from app.domain.service.dataset_loader import DatasetLoader
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ml", tags=["뉴스 ML 모델 훈련"])

# 서비스 인스턴스
ml_service = NewsMLService()
dataset_loader = DatasetLoader()

# 기본 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DATASETS_DIR = os.path.join(BASE_DIR, "app", "sample_datasets")
TRAINING_DATA_DIR = os.path.join(BASE_DIR, "data", "training")

def resolve_file_path(file_path: str, base_dir: str) -> str:
    """파일 경로를 절대 경로로 변환"""
    logger.info(f"경로 해결 시작: {file_path}, 기본 디렉토리: {base_dir}")
    
    # 이미 절대 경로인 경우
    if os.path.isabs(file_path):
        if os.path.exists(file_path):
            logger.info(f"절대 경로 확인됨: {file_path}")
            return file_path
    
    # 상대 경로 정리
    if file_path.startswith("./"):
        file_path = file_path[2:]
    
    # 여러 위치에서 파일 검색
    search_paths = [
        os.path.join(base_dir, file_path),
        os.path.join(BASE_DIR, file_path),
        os.path.join(SAMPLE_DATASETS_DIR, os.path.basename(file_path)),
        os.path.join(TRAINING_DATA_DIR, os.path.basename(file_path))
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            logger.info(f"파일 발견: {path}")
            return path
    
    logger.warning(f"파일을 찾을 수 없음: {file_path}")
    return os.path.join(base_dir, file_path)

# 요청/응답 모델
class JSONTrainingRequest(BaseModel):
    """JSON 파일 기반 모델 훈련 요청"""
    model_config = {"protected_namespaces": ()}
    
    json_file_path: str = Field(..., description="JSON 데이터셋 파일 경로 (예: news_dataset_poc.json)")
    model_name: Optional[str] = Field(None, description="모델 이름 (미입력시 자동 생성)")
    apply_calibration: bool = Field(True, description="신뢰도 보정 적용 여부")
    temperature: float = Field(1.5, description="Temperature Scaling 값")
    max_confidence: float = Field(0.95, description="신뢰도 상한선")

@router.post("/train-models", summary="JSON으로 ESG 카테고리 + 감정 분석 모델 동시 훈련")
async def train_models_from_json(
    background_tasks: BackgroundTasks,
    request: JSONTrainingRequest
):
    """
    JSON 데이터셋으로부터 ESG 카테고리 분류 모델과 감정 분석 모델을 동시에 훈련합니다.
    
    - JSON 파일을 CSV로 변환 후 두 모델 모두 훈련
    - 신뢰도 보정 기능 포함 (기본값: 적용)
    - 백그라운드에서 실행되어 즉시 응답
    """
    try:
        # 파일 경로 해결
        resolved_path = resolve_file_path(request.json_file_path, SAMPLE_DATASETS_DIR)
        
        logger.info(f"JSON 파인튜닝 시작 - 파일: {resolved_path}, 모델명: {request.model_name}")
        
        # 파일 존재 확인
        if not os.path.exists(resolved_path):
            available_files = []
            if os.path.exists(SAMPLE_DATASETS_DIR):
                available_files = [f for f in os.listdir(SAMPLE_DATASETS_DIR) if f.endswith('.json')]
            
            raise HTTPException(
                status_code=404, 
                detail=f"JSON 파일을 찾을 수 없습니다: {request.json_file_path}\n"
                       f"검색된 경로: {resolved_path}\n"
                       f"사용 가능한 JSON 파일: {available_files}"
            )
        
        # JSON 형식 검증
        validation_result = await dataset_loader.validate_json_format(resolved_path)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"JSON 형식이 올바르지 않습니다: {validation_result}"
            )
        
        # JSON을 CSV로 변환
        conversion_result = await dataset_loader.convert_json_to_training_format(resolved_path)
        
        category_dataset = conversion_result["files"]["category_dataset"]
        sentiment_dataset = conversion_result["files"]["sentiment_dataset"]
        
        # 모델 이름 생성
        if not request.model_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(resolved_path))[0]
            model_name = f"{base_name}_{timestamp}"
        else:
            model_name = request.model_name
        
        category_model_name = f"{model_name}_category"
        sentiment_model_name = f"{model_name}_sentiment"
        
        # 백그라운드에서 두 모델 모두 훈련 (신뢰도 보정 포함)
        if request.apply_calibration:
            background_tasks.add_task(
                ml_service.train_calibrated_model,
                category_dataset, 
                category_model_name,
                "category",
                True,
                request.temperature,
                request.max_confidence
            )
            background_tasks.add_task(
                ml_service.train_calibrated_model,
                sentiment_dataset, 
                sentiment_model_name,
                "sentiment", 
                True,
                request.temperature,
                request.max_confidence
            )
        else:
            background_tasks.add_task(ml_service.train_category_classifier, category_dataset, category_model_name)
            background_tasks.add_task(ml_service.train_sentiment_analyzer, sentiment_dataset, sentiment_model_name)
        
        return JSONResponse(
            status_code=202,
            content={
                "success": True,
                "message": "ESG 카테고리 + 감정 분석 모델 훈련이 백그라운드에서 시작되었습니다",
                "training_info": {
                    "json_file": resolved_path,
                    "category_model_name": category_model_name,
                    "sentiment_model_name": sentiment_model_name,
                    "apply_calibration": request.apply_calibration,
                    "temperature": request.temperature if request.apply_calibration else None,
                    "max_confidence": request.max_confidence if request.apply_calibration else None
                },
                "status_check_url": "/api/v1/ml/training-status"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON 파인튜닝 요청 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/convert-json-to-csv", summary="JSON 데이터셋을 CSV로 변환")
async def convert_json_to_csv(json_file_path: str):
    """JSON 데이터셋을 훈련용 CSV 파일로 변환합니다."""
    try:
        resolved_path = resolve_file_path(json_file_path, SAMPLE_DATASETS_DIR)
        
        if not os.path.exists(resolved_path):
            raise HTTPException(status_code=404, detail=f"JSON 파일을 찾을 수 없습니다: {json_file_path}")
        
        result = await dataset_loader.convert_json_to_training_format(resolved_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "JSON 데이터셋이 CSV로 변환되었습니다",
                "conversion_result": result
            }
        )
        
    except Exception as e:
        logger.error(f"JSON to CSV 변환 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"변환 오류: {str(e)}")

@router.get("/sample-datasets", summary="샘플 데이터셋 목록 조회")
async def list_sample_datasets():
    """사용 가능한 샘플 데이터셋 목록을 조회합니다."""
    try:
        datasets = []
        
        if os.path.exists(SAMPLE_DATASETS_DIR):
            for file in os.listdir(SAMPLE_DATASETS_DIR):
                if file.endswith('.json'):
                    file_path = os.path.join(SAMPLE_DATASETS_DIR, file)
                    file_size = os.path.getsize(file_path)
                    datasets.append({
                        "filename": file,
                        "path": file_path,
                        "size_bytes": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "datasets": datasets,
                "total_count": len(datasets)
            }
        )
        
    except Exception as e:
        logger.error(f"샘플 데이터셋 목록 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"목록 조회 오류: {str(e)}")

@router.post("/validate-json", summary="JSON 데이터셋 형식 검증")
async def validate_json_dataset(json_file_path: str):
    """JSON 데이터셋의 형식이 올바른지 검증합니다."""
    try:
        resolved_path = resolve_file_path(json_file_path, SAMPLE_DATASETS_DIR)
        
        if not os.path.exists(resolved_path):
            raise HTTPException(status_code=404, detail=f"JSON 파일을 찾을 수 없습니다: {json_file_path}")
        
        validation_result = await dataset_loader.validate_json_format(resolved_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "validation_result": validation_result
            }
        )
        
    except Exception as e:
        logger.error(f"JSON 검증 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"검증 오류: {str(e)}")

@router.get("/training-status", summary="훈련 상태 조회")
async def get_training_status():
    """현재 진행 중인 모델 훈련 상태를 조회합니다."""
    try:
        status = await ml_service.get_training_status()
        return JSONResponse(status_code=200, content=status)
    except Exception as e:
        logger.error(f"훈련 상태 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상태 조회 오류: {str(e)}")

@router.get("/trained-models", summary="훈련된 모델 목록 조회")
async def list_trained_models():
    """훈련이 완료된 모델 목록을 조회합니다."""
    try:
        models = await ml_service.list_trained_models()
        return JSONResponse(status_code=200, content=models)
    except Exception as e:
        logger.error(f"모델 목록 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"목록 조회 오류: {str(e)}")

@router.get("/datasets", summary="데이터셋 목록 조회")
async def list_datasets():
    """훈련 데이터 디렉토리의 CSV 파일 목록을 조회합니다."""
    try:
        datasets = []
        
        if os.path.exists(TRAINING_DATA_DIR):
            for file in os.listdir(TRAINING_DATA_DIR):
                if file.endswith('.csv'):
                    file_path = os.path.join(TRAINING_DATA_DIR, file)
                    file_size = os.path.getsize(file_path)
                    datasets.append({
                        "filename": file,
                        "path": file_path,
                        "size_bytes": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "datasets": datasets,
                "total_count": len(datasets),
                "training_data_dir": TRAINING_DATA_DIR
            }
        )
        
    except Exception as e:
        logger.error(f"데이터셋 목록 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"목록 조회 오류: {str(e)}")

@router.get("/health", summary="서비스 상태 확인")
async def health_check():
    """서비스 상태를 확인합니다."""
    try:
        import torch
        from transformers import __version__ as transformers_version
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "status": "healthy",
                "pytorch_version": torch.__version__,
                "transformers_version": transformers_version,
                "cuda_available": torch.cuda.is_available(),
                "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "current_device": str(torch.cuda.current_device()) if torch.cuda.is_available() else "cpu"
            }
        )
    except Exception as e:
        logger.error(f"헬스 체크 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "unhealthy",
                "error": str(e)
            }
        ) 