import os
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import torch

# wandb 비활성화
os.environ["WANDB_DISABLED"] = "true"
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from datasets import Dataset
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from tqdm import tqdm
import aiofiles

from ..service.dataset_loader import DatasetLoader
from ..service.calibration_service import ConfidenceCalibrationService, TemperatureScaling
from ...config.gpu_config import rtx2080_config as gpu_config

logger = logging.getLogger(__name__)

class NewsMLService:
    """뉴스 분류 모델 훈련 서비스 (RTX 2080 최적화)"""
    
    def __init__(self):
        # GPU 설정 적용
        self.gpu_config = gpu_config
        self.device = self.gpu_config.device
        logger.info(f"NewsML 훈련 서비스 초기화 - 디바이스: {self.device}")
        
        # GPU 상태 정보 출력
        if self.gpu_config:
            gpu_status = self.gpu_config.get_gpu_status()
            logger.info(f"GPU 상태 정보: {gpu_status}")
        else:
            logger.warning("GPU 설정을 사용할 수 없습니다")
        
        # 모델 경로 설정
        self.models_dir = "./models"
        self.data_dir = "./data"
        self.training_dir = "./data/training"
        self.output_dir = "./output"
        
        # 디렉토리 생성
        for dir_path in [self.models_dir, self.data_dir, self.training_dir, self.output_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 카테고리 정의 (5개 클래스: LABEL_0~LABEL_4)
        self.category_labels = ["환경(E)", "사회(S)", "지배구조(G)", "재무", "기타"]
        self.sentiment_labels = ["긍정", "부정", "중립"]
        
        # 모델 설정 (RTX 2080 최적화) - KLUE RoBERTa Large로 변경
        self.model_name = "klue/roberta-large"  # 한국어 RoBERTa Large 모델
        self.max_length = 512
        
        # GPU 설정에서 배치 크기 가져오기
        if self.gpu_config:
            training_args = self.gpu_config.get_training_args()
            self.batch_size = training_args["per_device_train_batch_size"]
            self.gradient_accumulation_steps = training_args["gradient_accumulation_steps"]
            self.fp16 = training_args["fp16"]
        else:
            self.batch_size = 8
            self.gradient_accumulation_steps = 2
            self.fp16 = True
        
        self.learning_rate = 1e-5  # RoBERTa Large는 더 낮은 학습률 사용
        self.num_epochs = 3
        
        # 데이터셋 로더 초기화
        self.dataset_loader = DatasetLoader()
        
        # 훈련 상태
        self.training_status = {
            "category_model": {"status": "not_started", "progress": 0},
            "sentiment_model": {"status": "not_started", "progress": 0}
        }
    

    
    async def train_category_classifier(self, dataset_file: str, model_name: str = None) -> Dict[str, Any]:
        """카테고리 분류 모델 훈련"""
        try:
            self.training_status["category_model"]["status"] = "training"
            self.training_status["category_model"]["progress"] = 0
            
            logger.info(f"카테고리 분류 모델 훈련 시작 - 모델명: {model_name}")
            
            # 데이터 로드
            df = pd.read_csv(dataset_file, encoding="utf-8")
            logger.info(f"훈련 데이터 로드: {len(df)}개")
            
            # 라벨 인코딩
            label_encoder = LabelEncoder()
            df["encoded_label"] = label_encoder.fit_transform(df["category_label"])
            
            # 데이터 분할 (안전한 방식)
            # 각 클래스별 데이터 개수 확인
            label_counts = df["encoded_label"].value_counts()
            min_samples = label_counts.min()
            
            # 모든 클래스에 최소 2개 이상의 샘플이 있는지 확인
            if min_samples >= 2:
                # Stratify 사용 가능
                train_texts, val_texts, train_labels, val_labels = train_test_split(
                    df["text"].tolist(),
                    df["encoded_label"].tolist(),
                    test_size=0.2,
                    random_state=42,
                    stratify=df["encoded_label"]
                )
                logger.info(f"Stratified split 사용 - 최소 클래스 샘플 수: {min_samples}")
            else:
                # Stratify 없이 랜덤 분할
                train_texts, val_texts, train_labels, val_labels = train_test_split(
                    df["text"].tolist(),
                    df["encoded_label"].tolist(),
                    test_size=0.2,
                    random_state=42
                )
                logger.warning(f"일부 클래스의 샘플 수가 부족하여 random split 사용 - 최소 클래스 샘플 수: {min_samples}")
                logger.info(f"클래스별 분포: {label_counts.to_dict()}")
            
            self.training_status["category_model"]["progress"] = 20
            
            # 토크나이저 로드
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # 텍스트 데이터 정제 및 검증
            def clean_texts(texts):
                cleaned_texts = []
                for i, text in enumerate(texts):
                    if text is None or not isinstance(text, str):
                        logger.warning(f"Invalid text at index {i}: {type(text)} - {text}")
                        cleaned_texts.append("빈 텍스트")  # 기본값으로 대체
                    elif len(str(text).strip()) == 0:
                        logger.warning(f"Empty text at index {i}")
                        cleaned_texts.append("빈 텍스트")  # 기본값으로 대체
                    else:
                        cleaned_texts.append(str(text).strip())
                return cleaned_texts
            
            # 텍스트 정제
            train_texts_clean = clean_texts(train_texts)
            val_texts_clean = clean_texts(val_texts)
            
            logger.info(f"텍스트 정제 완료 - 훈련: {len(train_texts_clean)}, 검증: {len(val_texts_clean)}")
            
            # 데이터셋 토크나이징
            train_encodings = tokenizer(train_texts_clean, truncation=True, padding=True, max_length=self.max_length)
            val_encodings = tokenizer(val_texts_clean, truncation=True, padding=True, max_length=self.max_length)
            
            # Dataset 객체 생성
            train_dataset = Dataset.from_dict({
                'input_ids': train_encodings['input_ids'],
                'attention_mask': train_encodings['attention_mask'],
                'labels': train_labels
            })
            
            val_dataset = Dataset.from_dict({
                'input_ids': val_encodings['input_ids'],
                'attention_mask': val_encodings['attention_mask'],
                'labels': val_labels
            })
            
            self.training_status["category_model"]["progress"] = 40
            
            # 모델 로드
            model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=len(self.category_labels)
            )
            
            # 훈련 설정 (RTX 2080 최적화)
            if model_name:
                output_dir = f"{self.models_dir}/{model_name}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = f"{self.models_dir}/category_classifier_{timestamp}"
            
            # 출력 디렉토리 생성 (권한 문제 방지)
            os.makedirs(output_dir, exist_ok=True)
            
            # GPU 최적화 설정 적용
            if self.gpu_config:
                training_args_config = self.gpu_config.get_training_args()
            else:
                training_args_config = {
                    "per_device_train_batch_size": 8,
                    "per_device_eval_batch_size": 8,
                    "gradient_accumulation_steps": 2,
                    "warmup_steps": 100,
                    "fp16": True,
                    "dataloader_pin_memory": True,
                    "dataloader_num_workers": 2,
                    "remove_unused_columns": False
                }
            
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=self.num_epochs,
                per_device_train_batch_size=training_args_config["per_device_train_batch_size"],
                per_device_eval_batch_size=training_args_config["per_device_eval_batch_size"],
                gradient_accumulation_steps=training_args_config["gradient_accumulation_steps"],
                learning_rate=self.learning_rate,
                warmup_steps=training_args_config.get("warmup_steps", 100),
                fp16=training_args_config["fp16"],
                dataloader_pin_memory=training_args_config["dataloader_pin_memory"],
                dataloader_num_workers=training_args_config["dataloader_num_workers"],
                remove_unused_columns=training_args_config["remove_unused_columns"],
                logging_dir=f"{output_dir}/logs",
                logging_steps=10,
                eval_strategy="no",  # 평가 비활성화로 권한 문제 방지
                save_strategy="no",  # 체크포인트 저장 완전 비활성화
                load_best_model_at_end=False,  # 체크포인트 없이 최종 모델만 사용
                report_to=[],  # wandb 비활성화
                save_safetensors=False,  # DTensor 오류 방지
            )
            
            # 데이터 콜레이터
            data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
            
            # 트레이너 설정
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                tokenizer=tokenizer,
                data_collator=data_collator,
            )
            
            self.training_status["category_model"]["progress"] = 60
            
            # 모델 훈련
            trainer.train()
            
            self.training_status["category_model"]["progress"] = 80
            
            # 모델 저장 (DTensor 오류 방지)
            try:
                trainer.save_model()
            except Exception as save_error:
                logger.warning(f"Trainer save_model 실패: {save_error}")
                try:
                    # 수동으로 모델 저장 (DTensor 오류 방지)
                    model.save_pretrained(output_dir, safe_serialization=False)
                except Exception as save_error2:
                    logger.warning(f"model.save_pretrained 실패: {save_error2}")
                    # 최후의 수단: PyTorch state_dict 직접 저장
                    import torch
                    os.makedirs(output_dir, exist_ok=True)
                    torch.save(model.state_dict(), f"{output_dir}/pytorch_model.bin")
                    model.config.save_pretrained(output_dir)
                    logger.info("PyTorch state_dict로 모델 저장 완료")
            
            tokenizer.save_pretrained(output_dir)
            
            # 라벨 인코더 저장 (5개 클래스 전체 매핑)
            label_encoder_path = f"{output_dir}/label_encoder.json"
            # 실제 사용된 라벨과 전체 5개 클래스 매핑
            label_mapping = {}
            for i, label in enumerate(label_encoder.classes_):
                label_mapping[i] = label
            # LABEL_4가 누락된 경우 "기타"로 추가
            if len(label_mapping) < 5:
                label_mapping[4] = "기타"
            
            with open(label_encoder_path, "w", encoding="utf-8") as f:
                json.dump(label_mapping, f, ensure_ascii=False, indent=2)
            
            # 평가
            predictions = trainer.predict(val_dataset)
            pred_labels = np.argmax(predictions.predictions, axis=1)
            
            accuracy = accuracy_score(val_labels, pred_labels)
            report = classification_report(
                val_labels, 
                pred_labels, 
                target_names=label_encoder.classes_,
                output_dict=True
            )
            
            # 혼동 행렬 생성
            cm = confusion_matrix(val_labels, pred_labels)
            
            # 결과 시각화 및 저장
            await self._save_training_results(
                "category",
                output_dir,
                float(accuracy),
                report,
                cm,
                list(label_encoder.classes_)
            )
            
            self.training_status["category_model"]["status"] = "completed"
            self.training_status["category_model"]["progress"] = 100
            
            logger.info(f"카테고리 분류 모델 훈련 완료 - 정확도: {accuracy:.4f}")
            
            return {
                "model_path": output_dir,
                "accuracy": accuracy,
                "classification_report": report,
                "confusion_matrix": cm.tolist() if hasattr(cm, 'tolist') else cm,
                "label_mapping": label_mapping,
                "training_samples": len(train_texts),
                "validation_samples": len(val_texts)
            }
            
        except Exception as e:
            self.training_status["category_model"]["status"] = "failed"
            logger.error(f"카테고리 분류 모델 훈련 중 오류: {str(e)}")
            raise
    
    async def train_sentiment_analyzer(self, dataset_file: str, model_name: str = None) -> Dict[str, Any]:
        """감정 분석 모델 훈련"""
        try:
            self.training_status["sentiment_model"]["status"] = "training"
            self.training_status["sentiment_model"]["progress"] = 0
            
            logger.info(f"감정 분석 모델 훈련 시작 - 모델명: {model_name}")
            
            # 데이터 로드
            df = pd.read_csv(dataset_file, encoding="utf-8")
            logger.info(f"훈련 데이터 로드: {len(df)}개")
            
            # 라벨 인코딩
            label_encoder = LabelEncoder()
            df["encoded_label"] = label_encoder.fit_transform(df["sentiment_label"])
            
            # 데이터 분할 (안전한 방식)
            # 각 클래스별 데이터 개수 확인
            label_counts = df["encoded_label"].value_counts()
            min_samples = label_counts.min()
            
            # 모든 클래스에 최소 2개 이상의 샘플이 있는지 확인
            if min_samples >= 2:
                # Stratify 사용 가능
                train_texts, val_texts, train_labels, val_labels = train_test_split(
                    df["text"].tolist(),
                    df["encoded_label"].tolist(),
                    test_size=0.2,
                    random_state=42,
                    stratify=df["encoded_label"]
                )
                logger.info(f"Stratified split 사용 - 최소 클래스 샘플 수: {min_samples}")
            else:
                # Stratify 없이 랜덤 분할
                train_texts, val_texts, train_labels, val_labels = train_test_split(
                    df["text"].tolist(),
                    df["encoded_label"].tolist(),
                    test_size=0.2,
                    random_state=42
                )
                logger.warning(f"일부 클래스의 샘플 수가 부족하여 random split 사용 - 최소 클래스 샘플 수: {min_samples}")
                logger.info(f"클래스별 분포: {label_counts.to_dict()}")
            
            self.training_status["sentiment_model"]["progress"] = 20
            
            # 토크나이저 로드
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # 텍스트 데이터 정제 및 검증
            def clean_texts(texts):
                cleaned_texts = []
                for i, text in enumerate(texts):
                    if text is None or not isinstance(text, str):
                        logger.warning(f"Invalid text at index {i}: {type(text)} - {text}")
                        cleaned_texts.append("빈 텍스트")  # 기본값으로 대체
                    elif len(str(text).strip()) == 0:
                        logger.warning(f"Empty text at index {i}")
                        cleaned_texts.append("빈 텍스트")  # 기본값으로 대체
                    else:
                        cleaned_texts.append(str(text).strip())
                return cleaned_texts
            
            # 텍스트 정제
            train_texts_clean = clean_texts(train_texts)
            val_texts_clean = clean_texts(val_texts)
            
            logger.info(f"텍스트 정제 완료 - 훈련: {len(train_texts_clean)}, 검증: {len(val_texts_clean)}")
            
            # 데이터셋 토크나이징
            train_encodings = tokenizer(train_texts_clean, truncation=True, padding=True, max_length=self.max_length)
            val_encodings = tokenizer(val_texts_clean, truncation=True, padding=True, max_length=self.max_length)
            
            # Dataset 객체 생성
            train_dataset = Dataset.from_dict({
                'input_ids': train_encodings['input_ids'],
                'attention_mask': train_encodings['attention_mask'],
                'labels': train_labels
            })
            
            val_dataset = Dataset.from_dict({
                'input_ids': val_encodings['input_ids'],
                'attention_mask': val_encodings['attention_mask'],
                'labels': val_labels
            })
            
            self.training_status["sentiment_model"]["progress"] = 40
            
            # 모델 로드
            model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=len(self.sentiment_labels)
            )
            
            # 훈련 설정 (RTX 2080 최적화)
            if model_name:
                output_dir = f"{self.models_dir}/{model_name}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = f"{self.models_dir}/sentiment_analyzer_{timestamp}"
            
            # GPU 최적화 설정 적용
            if self.gpu_config:
                training_args_config = self.gpu_config.get_training_args()
            else:
                training_args_config = {
                    "per_device_train_batch_size": 8,
                    "per_device_eval_batch_size": 8,
                    "gradient_accumulation_steps": 2,
                    "warmup_steps": 100,
                    "fp16": True,
                    "dataloader_pin_memory": True,
                    "dataloader_num_workers": 2,
                    "remove_unused_columns": False
                }
            
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=self.num_epochs,
                per_device_train_batch_size=training_args_config["per_device_train_batch_size"],
                per_device_eval_batch_size=training_args_config["per_device_eval_batch_size"],
                gradient_accumulation_steps=training_args_config["gradient_accumulation_steps"],
                learning_rate=self.learning_rate,
                warmup_steps=training_args_config.get("warmup_steps", 100),
                fp16=training_args_config["fp16"],
                dataloader_pin_memory=training_args_config["dataloader_pin_memory"],
                dataloader_num_workers=training_args_config["dataloader_num_workers"],
                remove_unused_columns=training_args_config["remove_unused_columns"],
                logging_dir=f"{output_dir}/logs",
                logging_steps=10,
                eval_strategy="no",  # 평가 비활성화로 권한 문제 방지
                save_strategy="no",  # 체크포인트 저장 완전 비활성화
                load_best_model_at_end=False,  # 체크포인트 없이 최종 모델만 사용
                report_to=[],  # wandb 비활성화
                save_safetensors=False,  # DTensor 오류 방지
            )
            
            # 데이터 콜레이터
            data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
            
            # 트레이너 설정
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                tokenizer=tokenizer,
                data_collator=data_collator,
            )
            
            self.training_status["sentiment_model"]["progress"] = 60
            
            # 모델 훈련
            trainer.train()
            
            self.training_status["sentiment_model"]["progress"] = 80
            
            # 모델 저장 (DTensor 오류 방지)
            try:
                trainer.save_model()
            except Exception as save_error:
                logger.warning(f"Trainer save_model 실패: {save_error}")
                try:
                    # 수동으로 모델 저장 (DTensor 오류 방지)
                    model.save_pretrained(output_dir, safe_serialization=False)
                except Exception as save_error2:
                    logger.warning(f"model.save_pretrained 실패: {save_error2}")
                    # 최후의 수단: PyTorch state_dict 직접 저장
                    import torch
                    os.makedirs(output_dir, exist_ok=True)
                    torch.save(model.state_dict(), f"{output_dir}/pytorch_model.bin")
                    model.config.save_pretrained(output_dir)
                    logger.info("PyTorch state_dict로 모델 저장 완료")
            
            tokenizer.save_pretrained(output_dir)
            
            # 라벨 인코더 저장 (3개 감정 클래스)
            label_encoder_path = f"{output_dir}/label_encoder.json"
            # 감정 분석은 3개 클래스로 고정
            label_mapping = {}
            for i, label in enumerate(label_encoder.classes_):
                label_mapping[i] = label
            
            with open(label_encoder_path, "w", encoding="utf-8") as f:
                json.dump(label_mapping, f, ensure_ascii=False, indent=2)
            
            # 평가
            predictions = trainer.predict(val_dataset)
            pred_labels = np.argmax(predictions.predictions, axis=1)
            
            accuracy = accuracy_score(val_labels, pred_labels)
            report = classification_report(
                val_labels, 
                pred_labels, 
                target_names=label_encoder.classes_,
                output_dict=True
            )
            
            # 혼동 행렬 생성
            cm = confusion_matrix(val_labels, pred_labels)
            
            # 결과 시각화 및 저장
            await self._save_training_results(
                "sentiment",
                output_dir,
                float(accuracy),
                report,
                cm,
                list(label_encoder.classes_)
            )
            
            self.training_status["sentiment_model"]["status"] = "completed"
            self.training_status["sentiment_model"]["progress"] = 100
            
            logger.info(f"감정 분석 모델 훈련 완료 - 정확도: {accuracy:.4f}")
            
            return {
                "model_path": output_dir,
                "accuracy": accuracy,
                "classification_report": report,
                "confusion_matrix": cm.tolist() if hasattr(cm, 'tolist') else cm,
                "label_mapping": label_mapping,
                "training_samples": len(train_texts),
                "validation_samples": len(val_texts)
            }
            
        except Exception as e:
            self.training_status["sentiment_model"]["status"] = "failed"
            logger.error(f"감정 분석 모델 훈련 중 오류: {str(e)}")
            raise
    
    async def _save_training_results(
        self, 
        model_type: str, 
        output_dir: str, 
        accuracy: float, 
        report: Dict, 
        cm: np.ndarray, 
        class_names: List[str]
    ):
        """훈련 결과 시각화 및 저장"""
        try:
            # 한글 폰트 설정 (한글 깨짐 방지)
            plt.rcParams['font.family'] = 'DejaVu Sans'
            plt.rcParams['axes.unicode_minus'] = False
            
            # 혼동 행렬 시각화
            plt.figure(figsize=(10, 8))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                       xticklabels=class_names, yticklabels=class_names)
            plt.title(f'{model_type.upper()} Model - Confusion Matrix')
            plt.ylabel('True Label')
            plt.xlabel('Predicted Label')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/confusion_matrix.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            # 분류 보고서를 DataFrame으로 변환하여 저장
            report_df = pd.DataFrame(report).transpose()
            report_df.to_csv(f"{output_dir}/classification_report.csv", encoding="utf-8")
            
            # 훈련 요약 보고서 생성
            summary = {
                "model_type": model_type,
                "accuracy": accuracy,
                "timestamp": datetime.now().isoformat(),
                "base_model": self.model_name,
                "num_classes": len(class_names),
                "class_names": class_names if isinstance(class_names, list) else list(class_names),
                "training_parameters": {
                    "max_length": self.max_length,
                    "batch_size": self.batch_size,
                    "learning_rate": self.learning_rate,
                    "num_epochs": self.num_epochs
                }
            }
            
            async with aiofiles.open(f"{output_dir}/training_summary.json", "w", encoding="utf-8") as f:
                await f.write(json.dumps(summary, ensure_ascii=False, indent=2))
            
            logger.info(f"{model_type} 모델 훈련 결과 저장 완료: {output_dir}")
            
        except Exception as e:
            logger.error(f"훈련 결과 저장 중 오류: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""
        
        # 기본 정제
        text = text.strip()
        text = ' '.join(text.split())  # 연속된 공백 제거
        
        # 너무 긴 텍스트는 자르기
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        return text
    
    async def get_training_status(self) -> Dict[str, Any]:
        """현재 훈련 상태 반환"""
        return {
            "training_status": self.training_status,
            "device": self.device,
            "model_config": {
                "base_model": self.model_name,
                "max_length": self.max_length,
                "batch_size": self.batch_size,
                "learning_rate": self.learning_rate,
                "num_epochs": self.num_epochs
            },
            "categories": self.category_labels,
            "sentiments": self.sentiment_labels
        }
    
    async def list_trained_models(self) -> Dict[str, Any]:
        """훈련된 모델 목록 반환"""
        try:
            models = []
            
            if os.path.exists(self.models_dir):
                for item in os.listdir(self.models_dir):
                    item_path = os.path.join(self.models_dir, item)
                    if os.path.isdir(item_path):
                        # 훈련 요약 파일 확인
                        summary_file = os.path.join(item_path, "training_summary.json")
                        if os.path.exists(summary_file):
                            try:
                                with open(summary_file, "r", encoding="utf-8") as f:
                                    summary = json.load(f)
                                    summary["model_path"] = item_path
                                    models.append(summary)
                            except Exception as e:
                                logger.error(f"모델 요약 로드 실패: {item_path}, {str(e)}")
            
            # 최신 순으로 정렬
            models.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return {
                "trained_models": models,
                "total_count": len(models)
            }
            
        except Exception as e:
            logger.error(f"훈련된 모델 목록 조회 중 오류: {str(e)}")
            return {"trained_models": [], "total_count": 0}
    

    
    async def export_model(self, model_path: str, export_format: str = "pytorch") -> Dict[str, Any]:
        """훈련된 모델을 다른 형식으로 내보내기"""
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"모델 경로를 찾을 수 없습니다: {model_path}")
            
            export_dir = f"{model_path}_exported_{export_format}"
            os.makedirs(export_dir, exist_ok=True)
            
            if export_format == "onnx":
                # ONNX 형식으로 내보내기 (구현 필요)
                logger.info("ONNX 내보내기는 향후 구현 예정")
                return {"message": "ONNX 내보내기는 향후 구현 예정"}
            
            elif export_format == "tensorflow":
                # TensorFlow 형식으로 내보내기 (구현 필요)
                logger.info("TensorFlow 내보내기는 향후 구현 예정")
                return {"message": "TensorFlow 내보내기는 향후 구현 예정"}
            
            else:
                # 기본 PyTorch 모델 복사
                import shutil
                shutil.copytree(model_path, export_dir, dirs_exist_ok=True)
                
            return {
                "export_path": export_dir,
                "format": export_format,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"모델 내보내기 중 오류: {str(e)}")
            raise 

    async def apply_confidence_calibration(
        self, 
        model_path: str, 
        validation_dataset_file: str = None,
        temperature: float = 1.5,
        max_confidence: float = 0.95
    ) -> Dict[str, Any]:
        """
        훈련된 모델에 신뢰도 보정 적용 (PyTorch 2.6+ 필요하므로 현재 버전에서는 건너뜀)
        
        Args:
            model_path: 훈련된 모델 경로
            validation_dataset_file: 검증 데이터셋 파일 (없으면 기본 검증셋 사용)
            temperature: Temperature scaling 값
            max_confidence: 최대 신뢰도 제한
        """
        try:
            logger.warning(f"신뢰도 보정을 건너뜁니다. PyTorch 2.6+ 필요 (현재: {torch.__version__})")
            
            # PyTorch 2.6+ 보안 요구사항으로 인해 현재 버전에서는 건너뜀
            return {
                "success": False,
                "message": f"PyTorch 2.6+ 필요 (현재: {torch.__version__})",
                "model_path": model_path,
                "calibration_applied": False,
                "skipped_reason": "pytorch_version_requirement"
            }
            
            # 원래 코드는 PyTorch 2.6+에서만 실행
            # 보정 서비스 초기화
            calibration_service = ConfidenceCalibrationService(max_confidence)
            
            # 모델과 토크나이저 로드 (PyTorch 2.6+에서만)
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model.to(self.device)
            model.eval()
            
            # 검증 데이터 로드
            if validation_dataset_file and os.path.exists(validation_dataset_file):
                df_val = pd.read_csv(validation_dataset_file, encoding="utf-8")
            else:
                # 기본 검증 데이터 사용 (훈련 데이터의 20%)
                logger.info("검증 데이터셋이 없어 기본 검증 데이터를 사용합니다")
                return {"error": "검증 데이터셋이 필요합니다"}
            
            # 라벨 인코더 로드
            label_encoder_path = os.path.join(model_path, "label_encoder.json")
            if os.path.exists(label_encoder_path):
                with open(label_encoder_path, 'r', encoding='utf-8') as f:
                    label_mapping = json.load(f)
            else:
                logger.warning("라벨 인코더를 찾을 수 없습니다")
                return {"error": "라벨 인코더를 찾을 수 없습니다"}
            
            # 텍스트와 라벨 준비
            texts = df_val["text"].tolist()
            true_labels = df_val["encoded_label"].tolist() if "encoded_label" in df_val.columns else df_val["category_label"].tolist()
            
            # 예측 수행 (보정 전)
            original_predictions = []
            original_confidences = []
            calibrated_predictions = []
            calibrated_confidences = []
            
            logger.info(f"검증 데이터 {len(texts)}개에 대해 신뢰도 보정 적용 중...")
            
            for i, text in enumerate(texts):
                if i % 100 == 0:
                    logger.info(f"진행률: {i}/{len(texts)} ({i/len(texts)*100:.1f}%)")
                
                # 텍스트 토크나이징
                inputs = tokenizer(
                    text, 
                    return_tensors="pt", 
                    truncation=True, 
                    padding=True, 
                    max_length=self.max_length
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # 모델 예측
                with torch.no_grad():
                    outputs = model(**inputs)
                    logits = outputs.logits[0]
                
                # 원본 예측 (보정 전)
                original_probs = torch.softmax(logits, dim=-1)
                original_pred = torch.argmax(original_probs, dim=-1).item()
                original_conf = torch.max(original_probs, dim=-1)[0].item()
                
                original_predictions.append(original_pred)
                original_confidences.append(original_conf)
                
                # 보정된 예측
                calibrated_pred, calibrated_conf, _ = calibration_service.calibrate_prediction(
                    logits, text, temperature, apply_confidence_cap=True
                )
                
                calibrated_predictions.append(calibrated_pred)
                calibrated_confidences.append(calibrated_conf)
            
            # 보정 성능 평가
            original_metrics = calibration_service.evaluate_calibration(
                original_confidences, true_labels, original_predictions
            )
            
            calibrated_metrics = calibration_service.evaluate_calibration(
                calibrated_confidences, true_labels, calibrated_predictions
            )
            
            # 보정 설정 저장
            calibration_config = {
                "temperature": temperature,
                "max_confidence": max_confidence,
                "calibration_applied": True,
                "boundary_keywords": calibration_service.boundary_keywords
            }
            
            calibration_config_path = os.path.join(model_path, "calibration_config.json")
            with open(calibration_config_path, 'w', encoding='utf-8') as f:
                json.dump(calibration_config, f, ensure_ascii=False, indent=2)
            
            logger.info("신뢰도 보정 적용 완료")
            
            return {
                "model_path": model_path,
                "calibration_config": calibration_config,
                "original_metrics": original_metrics,
                "calibrated_metrics": calibrated_metrics,
                "improvement": {
                    "ece_reduction": original_metrics["ece"] - calibrated_metrics["ece"],
                    "mce_reduction": original_metrics["mce"] - calibrated_metrics["mce"],
                    "confidence_reduction": original_metrics["avg_confidence"] - calibrated_metrics["avg_confidence"]
                },
                "validation_samples": len(texts)
            }
            
        except Exception as e:
            logger.error(f"신뢰도 보정 적용 중 오류: {str(e)}")
            raise Exception(f"신뢰도 보정 실패: {str(e)}")

    async def train_calibrated_model(
        self, 
        dataset_file: str, 
        model_name: str = None,
        model_type: str = "category",
        apply_calibration: bool = False,
        temperature: float = 1.5,
        max_confidence: float = 0.95
    ) -> Dict[str, Any]:
        """
        신뢰도 보정이 적용된 모델 훈련
        
        Args:
            dataset_file: 훈련 데이터셋 파일
            model_name: 모델 이름
            model_type: 모델 타입 ("category" 또는 "sentiment")
            apply_calibration: 신뢰도 보정 적용 여부
            temperature: Temperature scaling 값
            max_confidence: 최대 신뢰도 제한
        """
        try:
            logger.info(f"신뢰도 보정 모델 훈련 시작 - 타입: {model_type}, 보정: {apply_calibration}")
            
            # 기본 모델 훈련
            if model_type == "category":
                training_result = await self.train_category_classifier(dataset_file, model_name)
            elif model_type == "sentiment":
                training_result = await self.train_sentiment_analyzer(dataset_file, model_name)
            else:
                raise ValueError(f"지원하지 않는 모델 타입: {model_type}")
            
            if not apply_calibration:
                return training_result
            
            # 신뢰도 보정 적용
            model_path = training_result["model_path"]
            
            # 검증 데이터셋 파일 생성 (훈련 데이터의 일부 사용)
            df = pd.read_csv(dataset_file, encoding="utf-8")
            val_size = max(100, int(len(df) * 0.2))  # 최소 100개 또는 20%
            df_val = df.sample(n=min(val_size, len(df)), random_state=42)
            
            val_dataset_file = dataset_file.replace(".csv", "_validation.csv")
            df_val.to_csv(val_dataset_file, index=False, encoding="utf-8")
            
            # 신뢰도 보정 적용
            calibration_result = await self.apply_confidence_calibration(
                model_path, val_dataset_file, temperature, max_confidence
            )
            
            # 임시 검증 파일 삭제
            if os.path.exists(val_dataset_file):
                os.remove(val_dataset_file)
            
            # 결과 병합
            training_result.update({
                "calibration_applied": True,
                "calibration_result": calibration_result,
                "temperature": temperature,
                "max_confidence": max_confidence
            })
            
            logger.info("신뢰도 보정 모델 훈련 완료")
            return training_result
            
        except Exception as e:
            logger.error(f"신뢰도 보정 모델 훈련 중 오류: {str(e)}")
            raise Exception(f"신뢰도 보정 모델 훈련 실패: {str(e)}") 