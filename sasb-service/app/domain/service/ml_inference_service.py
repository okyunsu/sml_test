import logging
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from ...config.settings import settings

class MLInferenceService:
    """
    Service for performing sentiment analysis by loading a local Hugging Face model.
    The model is loaded once and reused for all subsequent requests.
    """
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = None
        
        # Beat에서만 ML 모델 로딩 비활성화 (스케줄링만 담당)
        disable_ml = os.getenv("DISABLE_ML_MODEL", "false").lower() == "true"
        if disable_ml:
            logging.info("ML 모델 로딩이 비활성화되었습니다 (Beat 컨테이너)")
            return
            
        if settings.MODEL_NAME and settings.MODEL_BASE_PATH:
            try:
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                logging.info(f"Using device: {self.device}")
                
                # SASB 서비스에서는 감성평가 모델만 사용
                model_path = os.path.join(settings.MODEL_BASE_PATH, f"{settings.MODEL_NAME}_sentiment")
                
                if os.path.isdir(model_path):
                    # 메모리 효율적인 모델 로딩 설정
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_path,
                        local_files_only=True,
                        use_fast=True
                    )
                    self.model = AutoModelForSequenceClassification.from_pretrained(
                        model_path,
                        local_files_only=True,
                        torch_dtype=torch.float32  # CPU에서는 float32 사용
                    ).to(self.device)
                    logging.info(f"'{settings.MODEL_NAME}' 감성평가 모델을 '{model_path}' 경로에서 성공적으로 불러왔습니다.")
                else:
                    logging.error(f"모델 경로를 찾을 수 없거나 디렉토리가 아닙니다: {model_path}")

            except Exception as e:
                logging.error(f"모델 로딩 중 에러 발생: {e}", exc_info=True)
        else:
            logging.warning("MODEL_NAME 또는 MODEL_BASE_PATH가 설정되지 않아 모델을 로드하지 않았습니다.")


    def analyze_sentiment(self, text: str) -> dict:
        """
        Analyzes the sentiment of a single text string.
        """
        if not self.model or not self.tokenizer:
            logging.warning("모델이 로드되지 않아 감성 분석을 중립으로 처리합니다.")
            # 🎯 모델 로드 실패 시 안전한 기본값 반환
            return {"sentiment": "중립", "confidence": 0.0}
            
        if not text or not isinstance(text, str) or not text.strip():
            # 🎯 빈 텍스트는 중립으로 처리 (SentimentResult 호환)
            return {"sentiment": "중립", "confidence": 0.0}

        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)

            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
            confidence, predicted_class_id = torch.max(probabilities, dim=-1)
            
            sentiment = "unknown"
            if hasattr(self.model, 'config') and self.model.config and self.model.config.id2label:
                raw_sentiment = self.model.config.id2label[predicted_class_id.item()]
                sentiment = self._convert_sentiment_label(raw_sentiment)
            else:
                logging.warning("model.config.id2label을 찾을 수 없습니다. 예측된 클래스 ID를 대신 반환합니다.")
                class_id = predicted_class_id.item()
                sentiment = self._convert_sentiment_label(str(class_id))

            return {
                "sentiment": sentiment,
                "confidence": confidence.item()
            }
        except Exception as e:
            logging.error(f"Sentiment analysis 중 에러 발생: '{e}'\nInput text: {text}", exc_info=True)
            # 🎯 에러 시 안전한 기본값 반환 (SentimentResult 호환)
            return {"sentiment": "중립", "confidence": 0.0}

    def _convert_sentiment_label(self, raw_sentiment: str) -> str:
        """
        LABEL_0, LABEL_1, LABEL_2 또는 숫자를 사람이 읽기 쉬운 형태로 변환
        
        일반적인 3-class sentiment 분류:
        - LABEL_0 / 0 = 부정 (negative)
        - LABEL_1 / 1 = 긍정 (positive) 
        - LABEL_2 / 2 = 중립 (neutral)
        """
        # 대소문자 구분 없이 처리
        label = raw_sentiment.upper().strip()
        
        # LABEL_X 형태 처리 (수정된 매핑)
        if label == "LABEL_0" or label == "0":
            return "긍정"  # 수정: LABEL_0 = 긍정
        elif label == "LABEL_1" or label == "1":
            return "부정"  # 수정: LABEL_1 = 부정
        elif label == "LABEL_2" or label == "2":
            return "중립"
        
        # 이미 변환된 형태인지 확인
        elif label in ["부정", "NEGATIVE", "NEG"]:
            return "부정"
        elif label in ["긍정", "POSITIVE", "POS"]:
            return "긍정"
        elif label in ["중립", "NEUTRAL", "NEU"]:
            return "중립"
        
        # 알 수 없는 라벨의 경우 로깅하고 원본 반환
        else:
            logging.warning(f"알 수 없는 sentiment 라벨: '{raw_sentiment}' → 중립으로 처리")
            return "중립"

    def get_device(self):
        """Returns the device (cpu/cuda) being used by the model."""
        return self.device