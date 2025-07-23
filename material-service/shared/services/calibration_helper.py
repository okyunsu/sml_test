"""
보정(Calibration) 헬퍼 모듈
Newstun Service에서 사용하는 복잡한 신뢰도 보정 로직을 지원하는 헬퍼 함수들
"""
import json
import logging
import os
import pandas as pd
import torch
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class CalibrationValidator:
    """신뢰도 보정 유효성 검사 헬퍼 클래스"""
    
    @staticmethod
    def check_pytorch_version() -> Dict[str, Any]:
        """PyTorch 버전 호환성 체크"""
        pytorch_version = torch.__version__
        is_compatible = False  # 현재는 모든 버전에서 False로 설정
        
        logger.warning(f"신뢰도 보정을 건너뜁니다. PyTorch 2.6+ 필요 (현재: {pytorch_version})")
        
        return {
            "success": False,
            "message": f"PyTorch 2.6+ 필요 (현재: {pytorch_version})",
            "calibration_applied": False,
            "skipped_reason": "pytorch_version_requirement",
            "is_compatible": is_compatible
        }
    
    @staticmethod
    def validate_model_path(model_path: str) -> bool:
        """모델 경로 유효성 검사"""
        if not os.path.exists(model_path):
            logger.error(f"모델 경로가 존재하지 않습니다: {model_path}")
            return False
        
        label_encoder_path = os.path.join(model_path, "label_encoder.json")
        if not os.path.exists(label_encoder_path):
            logger.warning("라벨 인코더를 찾을 수 없습니다")
            return False
        
        return True
    
    @staticmethod
    def validate_validation_dataset(validation_dataset_file: Optional[str]) -> bool:
        """검증 데이터셋 유효성 검사"""
        if validation_dataset_file and os.path.exists(validation_dataset_file):
            return True
        else:
            logger.info("검증 데이터셋이 없어 기본 검증 데이터를 사용합니다")
            return False

class ModelResourceManager:
    """모델 리소스 관리 헬퍼 클래스"""
    
    @staticmethod
    def load_model_and_tokenizer(model_path: str, device):
        """모델과 토크나이저 로드"""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model.to(device)
            model.eval()
            
            logger.info(f"모델과 토크나이저 로드 완료: {model_path}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise
    
    @staticmethod
    def load_label_encoder(model_path: str) -> Dict[str, Any]:
        """라벨 인코더 로드"""
        try:
            label_encoder_path = os.path.join(model_path, "label_encoder.json")
            with open(label_encoder_path, 'r', encoding='utf-8') as f:
                label_mapping = json.load(f)
            
            logger.info("라벨 인코더 로드 완료")
            return label_mapping
            
        except Exception as e:
            logger.error(f"라벨 인코더 로드 실패: {e}")
            raise
    
    @staticmethod
    def prepare_validation_data(validation_dataset_file: str) -> Tuple[List[str], List[int]]:
        """검증 데이터 준비"""
        try:
            df_val = pd.read_csv(validation_dataset_file, encoding="utf-8")
            
            texts = df_val["text"].tolist()
            true_labels = (
                df_val["encoded_label"].tolist() 
                if "encoded_label" in df_val.columns 
                else df_val["category_label"].tolist()
            )
            
            logger.info(f"검증 데이터 준비 완료: {len(texts)}개 샘플")
            return texts, true_labels
            
        except Exception as e:
            logger.error(f"검증 데이터 준비 실패: {e}")
            raise

class CalibrationProcessor:
    """신뢰도 보정 처리 헬퍼 클래스"""
    
    @staticmethod
    def process_single_prediction(
        text: str,
        model,
        tokenizer,
        calibration_service,
        device,
        max_length: int = 512,
        temperature: float = 1.5
    ) -> Tuple[int, float, int, float]:
        """단일 텍스트에 대한 원본/보정 예측 처리"""
        try:
            # 텍스트 토크나이징
            inputs = tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=max_length
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # 모델 예측
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits[0]
            
            # 원본 예측 (보정 전)
            original_probs = torch.softmax(logits, dim=-1)
            original_pred = torch.argmax(original_probs, dim=-1).item()
            original_conf = torch.max(original_probs, dim=-1)[0].item()
            
            # 보정된 예측
            calibrated_pred, calibrated_conf, _ = calibration_service.calibrate_prediction(
                logits, text, temperature, apply_confidence_cap=True
            )
            
            return original_pred, original_conf, calibrated_pred, calibrated_conf
            
        except Exception as e:
            logger.error(f"예측 처리 실패: {e}")
            raise
    
    @staticmethod
    def batch_process_predictions(
        texts: List[str],
        true_labels: List[int],
        model,
        tokenizer,
        calibration_service,
        device,
        max_length: int = 512,
        temperature: float = 1.5
    ) -> Dict[str, List]:
        """배치 예측 처리"""
        original_predictions = []
        original_confidences = []
        calibrated_predictions = []
        calibrated_confidences = []
        
        logger.info(f"검증 데이터 {len(texts)}개에 대해 신뢰도 보정 적용 중...")
        
        for i, text in enumerate(texts):
            if i % 100 == 0:
                logger.info(f"진행률: {i}/{len(texts)} ({i/len(texts)*100:.1f}%)")
            
            original_pred, original_conf, calibrated_pred, calibrated_conf = (
                CalibrationProcessor.process_single_prediction(
                    text, model, tokenizer, calibration_service, device, max_length, temperature
                )
            )
            
            original_predictions.append(original_pred)
            original_confidences.append(original_conf)
            calibrated_predictions.append(calibrated_pred)
            calibrated_confidences.append(calibrated_conf)
        
        return {
            "original_predictions": original_predictions,
            "original_confidences": original_confidences,
            "calibrated_predictions": calibrated_predictions,
            "calibrated_confidences": calibrated_confidences
        }

class CalibrationMetricsCalculator:
    """보정 성능 지표 계산 헬퍼 클래스"""
    
    @staticmethod
    def evaluate_calibration_performance(
        predictions_data: Dict[str, List],
        true_labels: List[int],
        calibration_service
    ) -> Dict[str, Dict[str, float]]:
        """보정 성능 평가"""
        try:
            # 원본 성능 평가
            original_metrics = calibration_service.evaluate_calibration(
                predictions_data["original_confidences"], 
                true_labels, 
                predictions_data["original_predictions"]
            )
            
            # 보정 성능 평가
            calibrated_metrics = calibration_service.evaluate_calibration(
                predictions_data["calibrated_confidences"], 
                true_labels, 
                predictions_data["calibrated_predictions"]
            )
            
            logger.info("보정 성능 평가 완료")
            return {
                "original_metrics": original_metrics,
                "calibrated_metrics": calibrated_metrics
            }
            
        except Exception as e:
            logger.error(f"보정 성능 평가 실패: {e}")
            raise
    
    @staticmethod
    def calculate_improvement_metrics(
        original_metrics: Dict[str, float],
        calibrated_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """개선 지표 계산"""
        return {
            "ece_reduction": original_metrics["ece"] - calibrated_metrics["ece"],
            "mce_reduction": original_metrics["mce"] - calibrated_metrics["mce"],
            "confidence_reduction": original_metrics["avg_confidence"] - calibrated_metrics["avg_confidence"]
        }

class CalibrationConfigManager:
    """보정 설정 관리 헬퍼 클래스"""
    
    @staticmethod
    def save_calibration_config(
        model_path: str,
        temperature: float,
        max_confidence: float,
        calibration_service
    ) -> str:
        """보정 설정 저장"""
        try:
            calibration_config = {
                "temperature": temperature,
                "max_confidence": max_confidence,
                "calibration_applied": True,
                "boundary_keywords": calibration_service.boundary_keywords
            }
            
            calibration_config_path = os.path.join(model_path, "calibration_config.json")
            with open(calibration_config_path, 'w', encoding='utf-8') as f:
                json.dump(calibration_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"보정 설정 저장 완료: {calibration_config_path}")
            return calibration_config_path
            
        except Exception as e:
            logger.error(f"보정 설정 저장 실패: {e}")
            raise
    
    @staticmethod
    def create_calibration_result(
        model_path: str,
        calibration_config: Dict[str, Any],
        metrics: Dict[str, Dict[str, float]],
        improvement: Dict[str, float],
        validation_samples: int
    ) -> Dict[str, Any]:
        """최종 보정 결과 생성"""
        return {
            "model_path": model_path,
            "calibration_config": calibration_config,
            "original_metrics": metrics["original_metrics"],
            "calibrated_metrics": metrics["calibrated_metrics"],
            "improvement": improvement,
            "validation_samples": validation_samples
        }

class CalibrationWorkflowManager:
    """보정 워크플로우 통합 관리 클래스"""
    
    @staticmethod
    async def execute_calibration_workflow(
        model_path: str,
        validation_dataset_file: Optional[str],
        temperature: float,
        max_confidence: float,
        calibration_service,
        device,
        max_length: int = 512
    ) -> Dict[str, Any]:
        """통합 보정 워크플로우 실행"""
        try:
            # 1. 유효성 검사
            if not CalibrationValidator.validate_model_path(model_path):
                return {"error": "모델 경로 또는 라벨 인코더를 찾을 수 없습니다"}
            
            if not CalibrationValidator.validate_validation_dataset(validation_dataset_file):
                return {"error": "검증 데이터셋이 필요합니다"}
            
            # 2. 리소스 로드
            model, tokenizer = ModelResourceManager.load_model_and_tokenizer(model_path, device)
            label_mapping = ModelResourceManager.load_label_encoder(model_path)
            texts, true_labels = ModelResourceManager.prepare_validation_data(validation_dataset_file)
            
            # 3. 예측 처리
            predictions_data = CalibrationProcessor.batch_process_predictions(
                texts, true_labels, model, tokenizer, calibration_service, device, max_length, temperature
            )
            
            # 4. 성능 평가
            metrics = CalibrationMetricsCalculator.evaluate_calibration_performance(
                predictions_data, true_labels, calibration_service
            )
            improvement = CalibrationMetricsCalculator.calculate_improvement_metrics(
                metrics["original_metrics"], metrics["calibrated_metrics"]
            )
            
            # 5. 설정 저장
            CalibrationConfigManager.save_calibration_config(
                model_path, temperature, max_confidence, calibration_service
            )
            
            # 6. 최종 결과 생성
            result = CalibrationConfigManager.create_calibration_result(
                model_path, 
                {"temperature": temperature, "max_confidence": max_confidence, "calibration_applied": True},
                metrics, 
                improvement, 
                len(texts)
            )
            
            logger.info("신뢰도 보정 워크플로우 완료")
            return result
            
        except Exception as e:
            logger.error(f"보정 워크플로우 실패: {e}")
            raise Exception(f"신뢰도 보정 실패: {str(e)}") 