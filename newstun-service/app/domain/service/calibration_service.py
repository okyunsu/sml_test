import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Any, List, Tuple
import logging
from sklearn.metrics import accuracy_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

class TemperatureScaling(nn.Module):
    """
    Temperature Scaling을 통한 모델 신뢰도 보정
    """
    def __init__(self, model):
        super(TemperatureScaling, self).__init__()
        self.model = model
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)  # 초기 temperature = 1.5
        
    def forward(self, input_ids, attention_mask):
        logits = self.model(input_ids=input_ids, attention_mask=attention_mask).logits
        return self.temperature_scale(logits)
    
    def temperature_scale(self, logits):
        """
        Temperature scaling 적용
        """
        return logits / self.temperature
    
    def set_temperature(self, valid_loader, device):
        """
        검증 데이터로 최적의 temperature 찾기
        """
        self.model.eval()
        logits_list = []
        labels_list = []
        
        with torch.no_grad():
            for batch in valid_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                logits = self.model(input_ids=input_ids, attention_mask=attention_mask).logits
                logits_list.append(logits)
                labels_list.append(labels)
        
        logits = torch.cat(logits_list).to(device)
        labels = torch.cat(labels_list).to(device)
        
        # Temperature 최적화
        optimizer = torch.optim.LBFGS([self.temperature], lr=0.01, max_iter=50)
        
        def eval():
            optimizer.zero_grad()
            loss = F.cross_entropy(self.temperature_scale(logits), labels)
            loss.backward()
            return loss
        
        optimizer.step(eval)
        
        # Temperature 값 제한 (0.1 ~ 10.0)
        self.temperature.data = torch.clamp(self.temperature.data, 0.1, 10.0)
        
        return self.temperature.item()

class ConfidenceCalibrationService:
    """
    모델 신뢰도 보정 서비스
    """
    
    def __init__(self, max_confidence: float = 0.95):
        self.max_confidence = max_confidence
        self.boundary_keywords = {
            's_fin': ["사업", "매출", "공급", "계약", "확장", "진출", "투자"],
            'e_fin': ["환경사업", "친환경", "에너지사업", "탄소배출권"],
            'g_s': ["이사회", "직원", "복지", "윤리"]
        }
        
    def calibrate_prediction(
        self, 
        logits: torch.Tensor, 
        text: str, 
        temperature: float = 1.5,
        apply_confidence_cap: bool = True
    ) -> Tuple[int, float, torch.Tensor]:
        """
        예측 결과 보정
        
        Args:
            logits: 모델 출력 로짓
            text: 입력 텍스트
            temperature: Temperature scaling 값
            apply_confidence_cap: 신뢰도 상한선 적용 여부
            
        Returns:
            predicted_class, confidence, probabilities
        """
        # Temperature scaling 적용
        scaled_logits = logits / temperature
        probabilities = F.softmax(scaled_logits, dim=-1)
        
        # 예측 클래스와 신뢰도
        predicted_class = torch.argmax(probabilities, dim=-1).item()
        base_confidence = torch.max(probabilities, dim=-1)[0].item()
        
        # 경계선 키워드 기반 신뢰도 조정
        adjusted_confidence = self._adjust_confidence_by_keywords(
            text, predicted_class, base_confidence, probabilities
        )
        
        # 텍스트 길이 기반 조정
        adjusted_confidence = self._adjust_confidence_by_length(
            text, adjusted_confidence
        )
        
        # Top-2 예측 간 차이 기반 조정
        adjusted_confidence = self._adjust_confidence_by_margin(
            probabilities, adjusted_confidence
        )
        
        # 신뢰도 상한선 적용
        if apply_confidence_cap:
            adjusted_confidence = min(adjusted_confidence, self.max_confidence)
        
        return predicted_class, adjusted_confidence, probabilities
    
    def _adjust_confidence_by_keywords(
        self, 
        text: str, 
        predicted_class: int, 
        confidence: float, 
        probabilities: torch.Tensor
    ) -> float:
        """
        경계선 키워드 기반 신뢰도 조정
        """
        text_lower = text.lower()
        
        # S/FIN 경계선 키워드
        if any(keyword in text_lower for keyword in self.boundary_keywords['s_fin']):
            if predicted_class in [1, 3]:  # S 또는 FIN 예측
                # 두 클래스의 확률 차이가 작으면 신뢰도 감소
                s_prob = probabilities[1].item() if len(probabilities) > 1 else 0
                fin_prob = probabilities[3].item() if len(probabilities) > 3 else 0
                
                if abs(s_prob - fin_prob) < 0.3:
                    confidence *= 0.7
                    logger.debug(f"S/FIN 경계선 키워드 감지 - 신뢰도 조정: {confidence:.3f}")
        
        # E/FIN 경계선 키워드
        if any(keyword in text_lower for keyword in self.boundary_keywords['e_fin']):
            if predicted_class in [0, 3]:  # E 또는 FIN 예측
                confidence *= 0.8
                logger.debug(f"E/FIN 경계선 키워드 감지 - 신뢰도 조정: {confidence:.3f}")
        
        # G/S 경계선 키워드
        if any(keyword in text_lower for keyword in self.boundary_keywords['g_s']):
            if predicted_class in [1, 2]:  # S 또는 G 예측
                confidence *= 0.8
                logger.debug(f"G/S 경계선 키워드 감지 - 신뢰도 조정: {confidence:.3f}")
        
        return confidence
    
    def _adjust_confidence_by_length(self, text: str, confidence: float) -> float:
        """
        텍스트 길이 기반 신뢰도 조정
        """
        text_length = len(text.strip())
        
        if text_length < 30:
            confidence *= 0.7
            logger.debug(f"짧은 텍스트({text_length}자) - 신뢰도 조정: {confidence:.3f}")
        elif text_length < 50:
            confidence *= 0.85
            logger.debug(f"중간 길이 텍스트({text_length}자) - 신뢰도 조정: {confidence:.3f}")
        
        return confidence
    
    def _adjust_confidence_by_margin(self, probabilities: torch.Tensor, confidence: float) -> float:
        """
        Top-2 예측 간 차이 기반 신뢰도 조정
        """
        # 상위 2개 확률 추출
        top2_probs, _ = torch.topk(probabilities, 2, dim=-1)
        margin = (top2_probs[0] - top2_probs[1]).item()
        
        # 차이가 작으면 불확실한 예측으로 간주
        if margin < 0.2:
            confidence *= 0.6
            logger.debug(f"낮은 예측 마진({margin:.3f}) - 신뢰도 조정: {confidence:.3f}")
        elif margin < 0.4:
            confidence *= 0.8
            logger.debug(f"중간 예측 마진({margin:.3f}) - 신뢰도 조정: {confidence:.3f}")
        
        return confidence
    
    def evaluate_calibration(
        self, 
        predictions: List[float], 
        true_labels: List[int], 
        predicted_labels: List[int],
        n_bins: int = 10
    ) -> Dict[str, float]:
        """
        모델 신뢰도 보정 성능 평가
        """
        # Reliability diagram을 위한 빈 생성
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        accuracies = []
        confidences = []
        bin_sizes = []
        
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # 현재 빈에 속하는 예측들
            in_bin = [(conf > bin_lower) & (conf <= bin_upper) for conf in predictions]
            prop_in_bin = sum(in_bin) / len(in_bin) if len(in_bin) > 0 else 0
            
            if prop_in_bin > 0:
                # 빈 내 정확도
                bin_predictions = [pred for i, pred in enumerate(predicted_labels) if in_bin[i]]
                bin_true_labels = [true for i, true in enumerate(true_labels) if in_bin[i]]
                bin_confidences = [conf for i, conf in enumerate(predictions) if in_bin[i]]
                
                if len(bin_predictions) > 0:
                    accuracy_in_bin = accuracy_score(bin_true_labels, bin_predictions)
                    avg_confidence_in_bin = np.mean(bin_confidences)
                    
                    accuracies.append(accuracy_in_bin)
                    confidences.append(avg_confidence_in_bin)
                    bin_sizes.append(len(bin_predictions))
        
        # Expected Calibration Error (ECE) 계산
        ece = 0
        total_samples = len(predictions)
        
        for acc, conf, size in zip(accuracies, confidences, bin_sizes):
            ece += (size / total_samples) * abs(acc - conf)
        
        # Maximum Calibration Error (MCE) 계산
        mce = max([abs(acc - conf) for acc, conf in zip(accuracies, confidences)]) if accuracies else 0
        
        return {
            'ece': ece,
            'mce': mce,
            'avg_confidence': np.mean(predictions),
            'accuracy': accuracy_score(true_labels, predicted_labels)
        }

class CalibratedModelWrapper:
    """
    보정된 모델 래퍼 클래스
    """
    
    def __init__(
        self, 
        model_path: str, 
        temperature: float = 1.5,
        max_confidence: float = 0.95
    ):
        self.model_path = model_path
        self.temperature = temperature
        self.calibration_service = ConfidenceCalibrationService(max_confidence)
        
        # 모델과 토크나이저 로드
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"보정된 모델 로드 완료 - Temperature: {temperature}, Max Confidence: {max_confidence}")
    
    def predict(self, text: str) -> Dict[str, Any]:
        """
        보정된 예측 수행
        """
        # 텍스트 토크나이징
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 모델 예측
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # 신뢰도 보정 적용
        predicted_class, confidence, probabilities = self.calibration_service.calibrate_prediction(
            logits[0], text, self.temperature
        )
        
        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'probabilities': probabilities.cpu().numpy().tolist(),
            'temperature_used': self.temperature,
            'calibration_applied': True
        } 