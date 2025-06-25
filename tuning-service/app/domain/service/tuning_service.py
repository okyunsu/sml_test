import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging



import torch
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering, AutoModelForCausalLM,
    TrainingArguments, Trainer, DataCollatorWithPadding
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset, load_dataset
import pandas as pd

from app.domain.model.tuning_request import TuningRequest, TaskType as RequestTaskType
from app.domain.model.tuning_response import (
    TuningStatus, JobStatus, ModelListResponse, ModelInfo, DeleteModelResponse
)
from app.domain.service.data_service import DataService
# RTX 2080 최적화 설정 import
from app.config.gpu_config import (
    setup_rtx2080_environment, 
    get_optimal_batch_size,
    monitor_gpu_memory,
    cleanup_gpu_memory,
    get_rtx2080_training_args,
    get_rtx2080_lora_config
)

logger = logging.getLogger(__name__)

class TuningService:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        # 로컬 환경 명확한 절대 경로 설정
        self.models_dir = r"C:\Users\bitcamp\Documents\321\tuning-service\models"
        self.data_service = DataService()
        
        # RTX 2080 환경 설정
        logger.info("🎮 RTX 2080 최적화 환경 설정 중...")
        gpu_available = setup_rtx2080_environment()
        if gpu_available:
            memory_info = monitor_gpu_memory()
            logger.info(f"💾 GPU 메모리 상태: {memory_info}")
        else:
            logger.warning("⚠️ GPU를 사용할 수 없습니다. CPU 모드로 실행됩니다.")
        
        # 허깅페이스 토큰 환경변수에서 가져오기
        self.hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if self.hf_token and self.hf_token.strip() == "your_token_here":
            self.hf_token = None  # 기본값인 경우 None으로 설정
        
        # 모델 디렉토리 생성
        os.makedirs(self.models_dir, exist_ok=True)
    
    async def run_fine_tuning(self, job_id: str, request: TuningRequest):
        """파인튜닝 실행"""
        try:
            # 작업 상태 초기화
            self.jobs[job_id] = {
                "status": JobStatus.RUNNING,
                "progress": 0.0,
                "created_at": datetime.now(),
                "started_at": datetime.now(),
                "request": request
            }
            
            logger.info(f"🚀 파인튜닝 작업 시작: {job_id}")
            logger.info(f"📋 모델: {request.model_name}, 타입: {request.model_type}, 작업: {request.task_type}")
            logger.info(f"📁 데이터 폴더: {request.reports_folder}")
            
            # 1. 데이터 준비
            await self._update_job_progress(job_id, 5.0, "📊 데이터 준비 시작...")
            logger.info(f"🔍 1단계: 데이터 준비 중...")
            dataset = await self._prepare_dataset(request)
            await self._update_job_progress(job_id, 25.0, "✅ 데이터 준비 완료")
            
            # 2. 모델 및 토크나이저 로드
            await self._update_job_progress(job_id, 30.0, "🤖 모델 로딩 시작...")
            logger.info(f"🔍 2단계: 모델 및 토크나이저 로딩 중...")
            model, tokenizer = await self._load_model_and_tokenizer(request)
            await self._update_job_progress(job_id, 40.0, "✅ 모델 로딩 완료")
            
            # 3. LoRA 설정 (필요시)
            if request.use_lora:
                await self._update_job_progress(job_id, 45.0, "⚙️ LoRA 설정 중...")
                logger.info(f"🔍 3단계: LoRA 설정 중...")
                # 계속 학습이 아닌 경우에만 새로운 LoRA 설정
                if not request.is_continual_learning:
                    model = self._setup_lora(model, request)
                    logger.info(f"✅ LoRA 설정 완료 (r={request.lora_r}, alpha={request.lora_alpha})")
                else:
                    logger.info("✅ 계속 학습: 기존 LoRA 어댑터 사용")
            
            # 4. 데이터 전처리
            await self._update_job_progress(job_id, 50.0, "🔄 데이터 전처리 시작...")
            logger.info(f"🔍 4단계: 데이터 전처리 중...")
            train_dataset, eval_dataset = await self._preprocess_data(
                dataset, tokenizer, request
            )
            logger.info(f"✅ 데이터 전처리 완료 (훈련: {len(train_dataset)}, 검증: {len(eval_dataset)})")
            
            # 5. 훈련 설정
            await self._update_job_progress(job_id, 60.0, "⚙️ 훈련 설정 중...")
            logger.info(f"🔍 5단계: 훈련 설정 중...")
            training_args = self._create_training_args(request, job_id)
            logger.info(f"✅ 훈련 설정 완료 (에포크: {request.num_epochs}, 배치: {request.batch_size}, LR: {request.learning_rate})")
            
            # 6. 트레이너 생성 및 훈련
            await self._update_job_progress(job_id, 70.0, "🏋️ 모델 훈련 시작...")
            logger.info(f"🔍 6단계: 트레이너 생성 및 훈련 시작...")
            logger.info(f"⏰ 예상 소요 시간: 약 1-3시간 (데이터 크기에 따라)")
            trainer = self._create_trainer(
                model, tokenizer, train_dataset, eval_dataset, training_args
            )
            
            # 훈련 실행
            logger.info(f"🚀 훈련 시작! 총 {request.num_epochs} 에포크 진행...")
            trainer.train()
            logger.info(f"🎉 훈련 완료!")
            
            # 7. 모델 저장
            await self._update_job_progress(job_id, 90.0, "💾 모델 저장 중...")
            logger.info(f"🔍 7단계: 모델 저장 중...")
            model_id = f"esg-{request.model_type}-{job_id[:8]}"
            model_path = os.path.join(self.models_dir, model_id)
            
            trainer.save_model(model_path)
            tokenizer.save_pretrained(model_path)
            logger.info(f"✅ 모델 저장 완료: {model_path}")
            
            # 메타데이터 저장
            await self._save_model_metadata(model_id, model_path, request)
            
            # 작업 완료
            self.jobs[job_id].update({
                "status": JobStatus.COMPLETED,
                "progress": 100.0,
                "completed_at": datetime.now(),
                "model_id": model_id,
                "model_path": model_path
            })
            
            total_time = datetime.now() - self.jobs[job_id]["started_at"]
            logger.info(f"🎊 파인튜닝 작업 완료! 총 소요시간: {total_time}")
            logger.info(f"📦 생성된 모델 ID: {model_id}")
            
        except Exception as e:
            logger.error(f"❌ 파인튜닝 작업 실패 ({job_id}): {str(e)}")
            self.jobs[job_id].update({
                "status": JobStatus.FAILED,
                "error_message": str(e),
                "completed_at": datetime.now()
            })
    
    async def _prepare_dataset(self, request: TuningRequest) -> Dataset:
        """데이터셋 준비 - 폴더 내 모든 PDF 파일 처리"""
        # 폴더 내 모든 PDF 파일 처리
        import glob
        pdf_files = glob.glob(os.path.join(request.reports_folder, "*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in folder: {request.reports_folder}")
        
        if not pdf_files:
            raise ValueError(f"폴더에 PDF 파일이 없습니다: {request.reports_folder}")
        
        df = await self.data_service.extract_data_from_reports(
            pdf_files, request.task_type
        )
        
        return Dataset.from_pandas(df)
    
    async def _load_model_and_tokenizer(self, request: TuningRequest):
        """모델과 토크나이저 로드"""
        # 토큰이 있으면 사용, 없으면 None
        token_kwargs = {"token": self.hf_token} if self.hf_token else {}
        
        # 계속 학습인 경우 기존 파인튜닝된 모델 로드
        if request.is_continual_learning and request.base_model_path:
            logger.info(f"🔍 계속 학습 모드: 기존 모델 로드 시도")
            logger.info(f"📁 models_dir: {self.models_dir}")
            logger.info(f"🎯 base_model_path: {request.base_model_path}")
            
            # 기존 파인튜닝된 모델의 경로 확인
            if not os.path.exists(request.base_model_path):
                # 모델 ID로 경로 찾기
                model_path = os.path.join(self.models_dir, request.base_model_path)
                logger.info(f"🔍 전체 모델 경로: {model_path}")
                logger.info(f"📂 경로 존재 여부: {os.path.exists(model_path)}")
                
                if os.path.exists(model_path):
                    request.base_model_path = model_path
                    logger.info(f"✅ 모델 경로 업데이트: {model_path}")
                else:
                    # 디버깅을 위해 models_dir 내용 확인
                    try:
                        models_list = os.listdir(self.models_dir) if os.path.exists(self.models_dir) else []
                        logger.error(f"❌ 사용 가능한 모델들: {models_list}")
                    except Exception as e:
                        logger.error(f"❌ models_dir 읽기 실패: {e}")
                    
                    raise ValueError(f"기존 모델을 찾을 수 없습니다: {request.base_model_path}")
            
            # 기존 모델의 메타데이터 로드
            metadata_path = os.path.join(request.base_model_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                base_model_name = metadata["base_model"]
            else:
                base_model_name = request.model_name
            
            # 베이스 모델과 토크나이저 로드
            tokenizer = AutoTokenizer.from_pretrained(base_model_name, **token_kwargs)
            
            if request.task_type == RequestTaskType.CLASSIFICATION:
                model = AutoModelForSequenceClassification.from_pretrained(
                    base_model_name, num_labels=2, **token_kwargs
                )
            elif request.task_type == RequestTaskType.QUESTION_ANSWERING:
                model = AutoModelForQuestionAnswering.from_pretrained(base_model_name, **token_kwargs)
            else:
                model = AutoModelForCausalLM.from_pretrained(base_model_name, **token_kwargs)
            
            # 기존 LoRA 어댑터 로드
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, request.base_model_path)
            
            # 계속 학습을 위해 모델을 훈련 모드로 설정하고 gradient 활성화
            model.train()
            for param in model.parameters():
                param.requires_grad = True
            
            # LoRA 파라미터만 훈련 가능하도록 설정
            model.print_trainable_parameters()
            
            logger.info("기존 파인튜닝된 모델 로드 완료 - gradient 활성화됨")
            
        else:
            # 새로운 파인튜닝인 경우 베이스 모델 로드
            tokenizer = AutoTokenizer.from_pretrained(request.model_name, **token_kwargs)
            
            if request.task_type == RequestTaskType.CLASSIFICATION:
                model = AutoModelForSequenceClassification.from_pretrained(
                    request.model_name, num_labels=2, **token_kwargs  # ESG/Non-ESG 분류
                )
            elif request.task_type == RequestTaskType.QUESTION_ANSWERING:
                model = AutoModelForQuestionAnswering.from_pretrained(request.model_name, **token_kwargs)
            else:
                model = AutoModelForCausalLM.from_pretrained(request.model_name, **token_kwargs)
        
        # 패딩 토큰 설정 (BERT의 경우 [PAD] 토큰 사용)
        if tokenizer.pad_token is None:
            if hasattr(tokenizer, 'pad_token_id') and tokenizer.pad_token_id is not None:
                tokenizer.pad_token = tokenizer.convert_ids_to_tokens(tokenizer.pad_token_id)
            else:
                tokenizer.pad_token = tokenizer.eos_token if tokenizer.eos_token else "[PAD]"
        
        return model, tokenizer
    
    def _setup_lora(self, model, request: TuningRequest):
        """RTX 2080 최적화 LoRA 설정"""
        if request.task_type == RequestTaskType.CLASSIFICATION:
            task_type = TaskType.SEQ_CLS
        elif request.task_type == RequestTaskType.QUESTION_ANSWERING:
            task_type = TaskType.QUESTION_ANS
        else:
            task_type = TaskType.CAUSAL_LM
        
        # RTX 2080 최적화 LoRA 설정 사용
        rtx2080_lora_config = get_rtx2080_lora_config()
        
        lora_config = LoraConfig(
            task_type=task_type,
            r=request.lora_r if hasattr(request, 'lora_r') and request.lora_r else rtx2080_lora_config["r"],
            lora_alpha=request.lora_alpha if hasattr(request, 'lora_alpha') and request.lora_alpha else rtx2080_lora_config["lora_alpha"],
            lora_dropout=request.lora_dropout if hasattr(request, 'lora_dropout') and request.lora_dropout else rtx2080_lora_config["lora_dropout"],
            target_modules=rtx2080_lora_config["target_modules"]
        )
        
        logger.info(f"🎯 RTX 2080 최적화 LoRA 설정: r={lora_config.r}, alpha={lora_config.lora_alpha}, dropout={lora_config.lora_dropout}")
        
        return get_peft_model(model, lora_config)
    
    async def _preprocess_data(self, dataset: Dataset, tokenizer, request: TuningRequest):
        """데이터 전처리"""
        def tokenize_function(examples):
            # 텍스트가 리스트인지 확인
            texts = examples["text"]
            if isinstance(texts, str):
                texts = [texts]
            elif isinstance(texts, list) and len(texts) > 0 and isinstance(texts[0], list):
                # 중첩 리스트인 경우 평탄화
                texts = [str(item) for sublist in texts for item in (sublist if isinstance(sublist, list) else [sublist])]
            
            # 토크나이징 (패딩은 나중에 data_collator에서 처리)
            tokenized = tokenizer(
                texts,
                truncation=True,
                padding=False,  # 배치별로 동적 패딩 사용
                max_length=request.max_length,
                return_tensors=None  # 리스트로 반환
            )
            
            # 텍스트 생성 모델의 경우 labels는 DataCollatorForLanguageModeling에서 자동 처리
            # 다른 태스크의 경우에만 라벨 설정
            if request.task_type != RequestTaskType.TEXT_GENERATION:
                if "labels" in examples:
                    labels = examples["labels"]
                elif "label" in examples:
                    labels = examples["label"]
                else:
                    labels = [0] * len(texts)  # 기본값
                
                # 라벨이 리스트가 아닌 경우 리스트로 변환
                if not isinstance(labels, list):
                    labels = [labels]
                
                tokenized["labels"] = labels
            
            return tokenized
        
        # 배치 처리로 토크나이징
        tokenized_dataset = dataset.map(
            tokenize_function, 
            batched=True,
            remove_columns=dataset.column_names  # 원본 컬럼 제거
        )
        
        # 필요한 컬럼이 있는지 확인
        print(f"Dataset columns after tokenization: {tokenized_dataset.column_names}")
        
        # 훈련/검증 분할
        split_dataset = tokenized_dataset.train_test_split(test_size=0.2, seed=42)
        return split_dataset["train"], split_dataset["test"]
    
    def _create_training_args(self, request: TuningRequest, job_id: str) -> TrainingArguments:
        """RTX 2080 최적화 훈련 인자 생성"""
        output_dir = request.output_dir or f"/app/models/temp_{job_id}"
        
        # RTX 2080 최적화 설정 가져오기
        rtx2080_args = get_rtx2080_training_args()
        
        # 배치 크기 최적화 (모델 타입에 따라)
        optimal_batch_size = get_optimal_batch_size(request.model_name, "train")
        train_batch_size = min(request.batch_size, optimal_batch_size) if hasattr(request, 'batch_size') and request.batch_size else optimal_batch_size
        
        eval_batch_size = get_optimal_batch_size(request.model_name, "eval")
        
        logger.info(f"🎯 RTX 2080 최적화 배치 크기: 훈련={train_batch_size}, 검증={eval_batch_size}")
        
        # GPU 메모리 모니터링
        memory_info = monitor_gpu_memory()
        if memory_info.get("usage_percent", 0) > 70:
            logger.warning(f"⚠️ GPU 메모리 사용량 높음: {memory_info.get('usage_percent')}%")
            cleanup_gpu_memory()
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            learning_rate=request.learning_rate,
            per_device_train_batch_size=train_batch_size,
            per_device_eval_batch_size=eval_batch_size,
            num_train_epochs=request.num_epochs,
            warmup_steps=rtx2080_args["warmup_steps"],
            logging_dir=f"/app/logs/{job_id}",
            logging_steps=rtx2080_args["logging_steps"],
            save_steps=rtx2080_args["save_steps"],
            eval_steps=rtx2080_args["eval_steps"],
            eval_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=rtx2080_args["load_best_model_at_end"],
            metric_for_best_model=rtx2080_args["metric_for_best_model"],
            greater_is_better=rtx2080_args["greater_is_better"],
            save_total_limit=rtx2080_args["save_total_limit"],
            gradient_accumulation_steps=rtx2080_args["gradient_accumulation_steps"],
            gradient_checkpointing=rtx2080_args["gradient_checkpointing"],
            fp16=rtx2080_args["fp16"],  # RTX 2080 FP16 지원
            dataloader_num_workers=rtx2080_args["dataloader_num_workers"],
            remove_unused_columns=rtx2080_args["remove_unused_columns"],
            report_to=[] if not request.wandb_project else ["wandb"],
            run_name=f"esg-tuning-{job_id[:8]}" if request.wandb_project else None,
        )
        
        logger.info(f"✅ RTX 2080 최적화 훈련 설정 완료 (FP16: {training_args.fp16}, Gradient Checkpointing: {training_args.gradient_checkpointing})")
        
        return training_args
    
    def _create_trainer(self, model, tokenizer, train_dataset, eval_dataset, training_args):
        """트레이너 생성"""
        # 텍스트 생성용 data collator 사용
        from transformers import DataCollatorForLanguageModeling
        
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,  # 자기회귀 언어 모델링 (GPT 스타일)
            pad_to_multiple_of=None
        )
        
        return Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            processing_class=tokenizer,  # tokenizer 대신 processing_class 사용
            data_collator=data_collator
        )
    
    async def _save_model_metadata(self, model_id: str, model_path: str, request: TuningRequest):
        """모델 메타데이터 저장"""
        metadata = {
            "model_id": model_id,
            "base_model": request.model_name,
            "model_type": request.model_type,
            "task_type": request.task_type,
            "created_at": datetime.now().isoformat(),
            "hyperparameters": {
                "learning_rate": request.learning_rate,
                "batch_size": request.batch_size,
                "num_epochs": request.num_epochs,
                "max_length": request.max_length,
                "use_lora": request.use_lora,
                "lora_r": request.lora_r if request.use_lora else None,
                "lora_alpha": request.lora_alpha if request.use_lora else None
            }
        }
        
        metadata_path = os.path.join(model_path, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    async def _update_job_progress(self, job_id: str, progress: float, message: str = ""):
        """작업 진행률 업데이트"""
        if job_id in self.jobs:
            self.jobs[job_id]["progress"] = progress
            if message:
                self.jobs[job_id]["current_message"] = message
    
    async def get_job_status(self, job_id: str) -> TuningStatus:
        """작업 상태 조회"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        
        return TuningStatus(
            job_id=job_id,
            status=job["status"],
            progress=job.get("progress", 0.0),
            created_at=job["created_at"],
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at"),
            error_message=job.get("error_message"),
            model_id=job.get("model_id"),
            model_path=job.get("model_path")
        )
    
    async def list_available_models(self) -> ModelListResponse:
        """사용 가능한 모델 목록 조회"""
        models = []
        
        if os.path.exists(self.models_dir):
            for model_dir in os.listdir(self.models_dir):
                model_path = os.path.join(self.models_dir, model_dir)
                metadata_path = os.path.join(model_path, "metadata.json")
                
                if os.path.isdir(model_path) and os.path.exists(metadata_path):
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    
                    # 파일 크기 계산
                    total_size = sum(
                        os.path.getsize(os.path.join(model_path, f))
                        for f in os.listdir(model_path)
                        if os.path.isfile(os.path.join(model_path, f))
                    )
                    
                    models.append(ModelInfo(
                        model_id=metadata["model_id"],
                        model_name=metadata["model_id"],
                        base_model=metadata["base_model"],
                        task_type=metadata["task_type"],
                        created_at=datetime.fromisoformat(metadata["created_at"]),
                        file_size=total_size
                    ))
        
        return ModelListResponse(
            models=models,
            total_count=len(models)
        )
    
    async def delete_model(self, model_id: str) -> DeleteModelResponse:
        """모델 삭제"""
        model_path = os.path.join(self.models_dir, model_id)
        
        if not os.path.exists(model_path):
            raise ValueError(f"Model {model_id} not found")
        
        # 모델 디렉토리 삭제
        import shutil
        shutil.rmtree(model_path)
        
        return DeleteModelResponse(
            model_id=model_id,
            message=f"모델 {model_id}가 성공적으로 삭제되었습니다.",
            deleted_at=datetime.now()
        ) 