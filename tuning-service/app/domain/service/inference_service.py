import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

import torch
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering, AutoModelForCausalLM,
    pipeline
)
from peft import PeftModel

from app.domain.model.tuning_request import InferenceRequest
from app.domain.model.tuning_response import InferenceResponse

logger = logging.getLogger(__name__)

class InferenceService:
    def __init__(self):
        self.models_dir = "/app/models"
        self.loaded_models: Dict[str, Dict[str, Any]] = {}
        
        # 허깅페이스 토큰 환경변수에서 가져오기
        self.hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if self.hf_token and self.hf_token.strip() == "your_token_here":
            self.hf_token = None  # 기본값인 경우 None으로 설정
    
    async def run_inference(self, request: InferenceRequest) -> InferenceResponse:
        """추론 실행"""
        start_time = time.time()
        
        try:
            # 모델 로드 (캐시된 모델 사용)
            model_info = await self._load_model(request.model_id)
            model = model_info["model"]
            tokenizer = model_info["tokenizer"]
            task_type = model_info["task_type"]
            
            # 추론 실행
            if task_type == "classification":
                result = await self._run_classification(
                    model, tokenizer, request.input_text
                )
            elif task_type == "question_answering":
                result = await self._run_question_answering(
                    model, tokenizer, request.input_text
                )
            else:
                result = await self._run_text_generation(
                    model, tokenizer, request
                )
            
            processing_time = time.time() - start_time
            
            return InferenceResponse(
                model_id=request.model_id,
                input_text=request.input_text,
                output_text=result.get("output_text", ""),
                confidence_score=result.get("confidence_score"),
                processing_time=processing_time,
                predicted_class=result.get("predicted_class"),
                class_probabilities=result.get("class_probabilities"),
                generation_config=result.get("generation_config"),
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Inference failed for model {request.model_id}: {str(e)}")
            raise ValueError(f"추론 실행 중 오류가 발생했습니다: {str(e)}")
    
    async def _load_model(self, model_id: str) -> Dict[str, Any]:
        """모델 로드 (캐싱 지원)"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]
        
        model_path = os.path.join(self.models_dir, model_id)
        metadata_path = os.path.join(model_path, "metadata.json")
        
        if not os.path.exists(model_path) or not os.path.exists(metadata_path):
            raise ValueError(f"모델 {model_id}를 찾을 수 없습니다.")
        
        # 토큰이 있으면 사용, 없으면 None
        token_kwargs = {"token": self.hf_token} if self.hf_token else {}
        
        # 메타데이터 로드
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # 토크나이저 로드
        tokenizer = AutoTokenizer.from_pretrained(model_path, **token_kwargs)
        
        # 모델 로드
        task_type = metadata["task_type"]
        base_model = metadata["base_model"]
        use_lora = metadata["hyperparameters"].get("use_lora", False)
        
        if task_type == "classification":
            if use_lora:
                base_model_obj = AutoModelForSequenceClassification.from_pretrained(
                    base_model, num_labels=2, **token_kwargs
                )
                model = PeftModel.from_pretrained(base_model_obj, model_path)
            else:
                model = AutoModelForSequenceClassification.from_pretrained(model_path, **token_kwargs)
        elif task_type == "question_answering":
            if use_lora:
                base_model_obj = AutoModelForQuestionAnswering.from_pretrained(base_model, **token_kwargs)
                model = PeftModel.from_pretrained(base_model_obj, model_path)
            else:
                model = AutoModelForQuestionAnswering.from_pretrained(model_path, **token_kwargs)
        else:
            if use_lora:
                base_model_obj = AutoModelForCausalLM.from_pretrained(base_model, **token_kwargs)
                model = PeftModel.from_pretrained(base_model_obj, model_path)
            else:
                model = AutoModelForCausalLM.from_pretrained(model_path, **token_kwargs)
        
        model.eval()
        
        model_info = {
            "model": model,
            "tokenizer": tokenizer,
            "task_type": task_type,
            "metadata": metadata
        }
        
        # 캐시에 저장
        self.loaded_models[model_id] = model_info
        
        logger.info(f"Model {model_id} loaded successfully")
        return model_info
    
    async def _run_classification(self, model, tokenizer, input_text: str) -> Dict[str, Any]:
        """분류 추론"""
        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        )
        
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class_id = predictions.argmax().item()
            confidence_score = predictions.max().item()
        
        # 클래스 레이블 (ESG/Non-ESG)
        class_labels = ["Non-ESG", "ESG"]
        predicted_class = class_labels[predicted_class_id]
        
        class_probabilities = {
            class_labels[i]: float(predictions[0][i])
            for i in range(len(class_labels))
        }
        
        return {
            "output_text": f"분류 결과: {predicted_class}",
            "predicted_class": predicted_class,
            "confidence_score": confidence_score,
            "class_probabilities": class_probabilities
        }
    
    async def _run_question_answering(self, model, tokenizer, input_text: str) -> Dict[str, Any]:
        """질의응답 추론"""
        # 입력 텍스트에서 질문과 컨텍스트 분리
        if "[SEP]" in input_text:
            question, context = input_text.split("[SEP]", 1)
        else:
            # 기본 컨텍스트 사용
            question = input_text
            context = "ESG 보고서 관련 질문입니다."
        
        inputs = tokenizer(
            question.strip(),
            context.strip(),
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        )
        
        with torch.no_grad():
            outputs = model(**inputs)
            start_scores = outputs.start_logits
            end_scores = outputs.end_logits
            
            start_idx = start_scores.argmax().item()
            end_idx = end_scores.argmax().item()
            
            if end_idx < start_idx:
                end_idx = start_idx
            
            answer_tokens = inputs["input_ids"][0][start_idx:end_idx+1]
            answer = tokenizer.decode(answer_tokens, skip_special_tokens=True)
            
            confidence_score = float(
                torch.nn.functional.softmax(start_scores, dim=-1).max() *
                torch.nn.functional.softmax(end_scores, dim=-1).max()
            )
        
        return {
            "output_text": answer if answer.strip() else "답변을 찾을 수 없습니다.",
            "confidence_score": confidence_score
        }
    
    async def _run_text_generation(self, model, tokenizer, request: InferenceRequest) -> Dict[str, Any]:
        """텍스트 생성 추론"""
        inputs = tokenizer(
            request.input_text,
            return_tensors="pt",
            truncation=True,
            padding=True
        )
        
        generation_config = {
            "max_length": request.max_length or 512,
            "temperature": request.temperature or 0.7,
            "top_p": request.top_p or 0.9,
            "do_sample": request.do_sample if request.do_sample is not None else True,
            "pad_token_id": tokenizer.eos_token_id
        }
        
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                **generation_config
            )
            
            generated_text = tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True
            )
        
        return {
            "output_text": generated_text,
            "generation_config": generation_config
        }
    
    def clear_model_cache(self, model_id: Optional[str] = None):
        """모델 캐시 정리"""
        if model_id:
            if model_id in self.loaded_models:
                del self.loaded_models[model_id]
                logger.info(f"Model {model_id} removed from cache")
        else:
            self.loaded_models.clear()
            logger.info("All models removed from cache") 