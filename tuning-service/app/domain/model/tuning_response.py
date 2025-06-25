from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TuningResponse(BaseModel):
    job_id: str = Field(..., description="파인튜닝 작업 ID")
    status: JobStatus = Field(..., description="작업 상태")
    message: str = Field(..., description="응답 메시지")
    model_id: Optional[str] = Field(None, description="생성된 모델 ID")
    created_at: datetime = Field(..., description="작업 생성 시간")
    estimated_completion_time: Optional[datetime] = Field(None, description="예상 완료 시간")
    
    class Config:
        use_enum_values = True

class TuningStatus(BaseModel):
    job_id: str = Field(..., description="파인튜닝 작업 ID")
    status: JobStatus = Field(..., description="작업 상태")
    progress: float = Field(..., description="진행률 (0-100)")
    current_epoch: Optional[int] = Field(None, description="현재 에포크")
    total_epochs: Optional[int] = Field(None, description="전체 에포크")
    current_step: Optional[int] = Field(None, description="현재 스텝")
    total_steps: Optional[int] = Field(None, description="전체 스텝")
    
    # 학습 메트릭
    train_loss: Optional[float] = Field(None, description="훈련 손실")
    eval_loss: Optional[float] = Field(None, description="검증 손실")
    learning_rate: Optional[float] = Field(None, description="현재 학습률")
    
    # 시간 정보
    created_at: datetime = Field(..., description="작업 생성 시간")
    started_at: Optional[datetime] = Field(None, description="작업 시작 시간")
    completed_at: Optional[datetime] = Field(None, description="작업 완료 시간")
    estimated_completion_time: Optional[datetime] = Field(None, description="예상 완료 시간")
    
    # 에러 정보
    error_message: Optional[str] = Field(None, description="에러 메시지")
    
    # 모델 정보
    model_id: Optional[str] = Field(None, description="생성된 모델 ID")
    model_path: Optional[str] = Field(None, description="모델 저장 경로")
    
    class Config:
        use_enum_values = True

class InferenceResponse(BaseModel):
    model_id: str = Field(..., description="사용된 모델 ID")
    input_text: str = Field(..., description="입력 텍스트")
    output_text: str = Field(..., description="생성된 텍스트")
    confidence_score: Optional[float] = Field(None, description="신뢰도 점수")
    processing_time: float = Field(..., description="처리 시간 (초)")
    
    # 분류 작업의 경우
    predicted_class: Optional[str] = Field(None, description="예측된 클래스")
    class_probabilities: Optional[Dict[str, float]] = Field(None, description="클래스별 확률")
    
    # 생성 작업의 경우
    generation_config: Optional[Dict[str, Any]] = Field(None, description="생성 설정")
    
    created_at: datetime = Field(..., description="추론 수행 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "esg-bert-v1",
                "input_text": "삼성전자의 ESG 경영 전략에 대해 설명해주세요.",
                "output_text": "삼성전자는 지속가능한 경영을 위해 환경, 사회, 지배구조 측면에서 다양한 전략을 추진하고 있습니다...",
                "confidence_score": 0.95,
                "processing_time": 1.23,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }

class ModelInfo(BaseModel):
    model_id: str = Field(..., description="모델 ID")
    model_name: str = Field(..., description="모델 이름")
    base_model: str = Field(..., description="베이스 모델")
    task_type: str = Field(..., description="작업 타입")
    created_at: datetime = Field(..., description="생성 시간")
    file_size: Optional[int] = Field(None, description="파일 크기 (bytes)")
    performance_metrics: Optional[Dict[str, float]] = Field(None, description="성능 지표")
    
class ModelListResponse(BaseModel):
    models: List[ModelInfo] = Field(..., description="모델 목록")
    total_count: int = Field(..., description="전체 모델 수")
    
class DeleteModelResponse(BaseModel):
    model_id: str = Field(..., description="삭제된 모델 ID")
    message: str = Field(..., description="삭제 결과 메시지")
    deleted_at: datetime = Field(..., description="삭제 시간") 