from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ModelType(str, Enum):
    BERT = "bert"
    ROBERTA = "roberta"
    ELECTRA = "electra"
    GPT = "gpt"
    T5 = "t5"

class TaskType(str, Enum):
    CLASSIFICATION = "classification"
    QUESTION_ANSWERING = "question_answering"
    TEXT_GENERATION = "text_generation"
    SUMMARIZATION = "summarization"

class TuningRequest(BaseModel):
    model_name: str = Field(..., description="베이스 모델명 (예: klue/bert-base)")
    model_type: str = Field(..., description="모델 타입 (bert, gpt, t5 등)")
    task_type: TaskType = Field(..., description="파인튜닝 작업 타입")
    
    # 데이터 관련
    reports_folder: str = Field(..., description="ESG 보고서 폴더 경로 (폴더 내 모든 PDF 처리)")
    
    # 계속 학습 관련 (새로 추가)
    base_model_path: Optional[str] = Field(None, description="기존 파인튜닝된 모델 경로 (계속 학습용)")
    is_continual_learning: bool = Field(False, description="계속 학습 여부")
    
    # 하이퍼파라미터
    learning_rate: float = Field(2e-5, description="학습률")
    batch_size: int = Field(16, description="배치 크기")
    num_epochs: int = Field(3, description="에포크 수")
    max_length: int = Field(512, description="최대 토큰 길이")
    warmup_steps: int = Field(500, description="워밍업 스텝")
    
    # LoRA 설정
    use_lora: bool = Field(True, description="LoRA 사용 여부")
    lora_r: int = Field(16, description="LoRA rank")
    lora_alpha: int = Field(32, description="LoRA alpha")
    lora_dropout: float = Field(0.1, description="LoRA dropout")
    
    # 훈련 설정
    save_steps: int = Field(500, description="모델 저장 간격")
    eval_steps: int = Field(500, description="평가 간격")
    output_dir: Optional[str] = Field(None, description="출력 디렉토리")
    
    # W&B 설정
    wandb_project: Optional[str] = Field(None, description="Weights & Biases 프로젝트명")
    
    class Config:
        use_enum_values = True

class InferenceRequest(BaseModel):
    model_id: str = Field(..., description="사용할 모델 ID")
    text: str = Field(..., description="추론할 텍스트")
    max_length: int = Field(512, description="최대 생성 길이")
    temperature: float = Field(0.7, description="생성 온도")
    top_p: float = Field(0.9, description="Top-p 샘플링")
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "esg-bert-v1",
                "text": "삼성전자의 ESG 경영 전략에 대해 설명해주세요.",
                "max_length": 512,
                "temperature": 0.7
            }
        } 