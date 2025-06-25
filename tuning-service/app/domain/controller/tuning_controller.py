from fastapi import BackgroundTasks, UploadFile
from typing import List
from datetime import datetime
import uuid

from app.domain.service.tuning_service import TuningService
from app.domain.service.inference_service import InferenceService
from app.domain.service.file_service import FileService
from app.domain.model.tuning_request import TuningRequest, InferenceRequest
from app.domain.model.tuning_response import (
    TuningResponse, InferenceResponse, TuningStatus, 
    ModelListResponse, DeleteModelResponse, JobStatus
)

class TuningController:
    def __init__(self):
        self.tuning_service = TuningService()
        self.inference_service = InferenceService()
        self.file_service = FileService()
    
    async def start_fine_tuning(
        self, 
        background_tasks: BackgroundTasks, 
        request: TuningRequest
    ) -> TuningResponse:
        """파인튜닝 작업 시작"""
        job_id = str(uuid.uuid4())
        
        # 백그라운드에서 파인튜닝 실행
        background_tasks.add_task(
            self.tuning_service.run_fine_tuning,
            job_id,
            request
        )
        
        return TuningResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="파인튜닝 작업이 시작되었습니다.",
            created_at=datetime.now()
        )
    
    async def upload_reports(self, files: List[UploadFile]) -> dict:
        """ESG 보고서 파일 업로드"""
        uploaded_files = []
        
        for file in files:
            file_path = await self.file_service.save_uploaded_file(file)
            uploaded_files.append({
                "filename": file.filename,
                "file_path": file_path,
                "size": file.size
            })
        
        return {
            "message": f"{len(uploaded_files)}개의 파일이 업로드되었습니다.",
            "files": uploaded_files
        }
    
    async def get_tuning_status(self, job_id: str) -> TuningStatus:
        """파인튜닝 작업 상태 조회"""
        return await self.tuning_service.get_job_status(job_id)
    
    async def inference(self, request: InferenceRequest) -> InferenceResponse:
        """파인튜닝된 모델로 추론 수행"""
        return await self.inference_service.run_inference(request)
    
    async def list_models(self) -> ModelListResponse:
        """사용 가능한 파인튜닝된 모델 목록 조회"""
        return await self.tuning_service.list_available_models()
    
    async def delete_model(self, model_id: str) -> DeleteModelResponse:
        """파인튜닝된 모델 삭제"""
        return await self.tuning_service.delete_model(model_id) 