# NewsTun Service

뉴스 텍스트 분류 및 감정 분석을 위한 머신러닝 훈련 서비스입니다.

## 📋 개요

이 서비스는 JSON 데이터셋을 사용한 뉴스 텍스트 분석 모델 훈련에 특화되어 있습니다:
- **ESG 카테고리 분류**: 환경(E), 사회(S), 지배구조(G), 재무(FIN), 기타 카테고리로 분류
- **감정 분석**: 긍정, 부정, 중립 감정 분석
- **JSON 데이터셋 훈련**: JSON 파일을 직접 사용한 모델 훈련
- **신뢰도 보정**: Temperature Scaling을 통한 과신뢰 문제 해결
- **GPU 최적화**: RTX 2080 하드웨어에 최적화된 훈련 설정

## 🚀 주요 기능

### 1. JSON 기반 통합 모델 훈련 (메인 기능)
- **엔드포인트**: `POST /api/v1/ml/train-models`
- **설명**: JSON 데이터셋으로 ESG 카테고리 + 감정 분석 모델 동시 훈련
- **특징**: 
  - 신뢰도 보정 자동 적용 (과신뢰 문제 해결)
  - 두 모델 동시 훈련으로 효율성 극대화
  - JSON → CSV 자동 변환
  - 백그라운드 실행으로 빠른 응답

```json
{
  "json_file_path": "news_dataset_poc.json",
  "model_name": "my_esg_model",
  "apply_calibration": true,
  "temperature": 1.5,
  "max_confidence": 0.95
}
```

### 2. 신뢰도 보정 시스템
- **Temperature Scaling**: 기본값 1.5로 과신뢰 완화
- **신뢰도 상한선**: 95%로 제한하여 현실적 신뢰도 제공
- **자동 조정**: 텍스트 특성에 따른 신뢰도 자동 조정

### 3. 데이터 관리
- **JSON 데이터셋 검증**: 파일 형식 및 데이터 품질 자동 검증
- **샘플 데이터셋 제공**: `app/sample_datasets/news_dataset_poc.json`
- **자동 변환**: JSON → CSV 변환 및 훈련 데이터 생성

## 🔧 API 엔드포인트

### 핵심 기능
- `POST /api/v1/ml/train-models` - **JSON으로 ESG 카테고리 + 감정 분석 모델 동시 훈련**
  - **파라미터**: 
    - `json_file_path`: JSON 파일 경로
    - `model_name` (선택): 모델 이름 (미지정시 자동 생성)
    - `apply_calibration`: 신뢰도 보정 적용 여부 (기본: true)
    - `temperature`: Temperature Scaling 값 (기본: 1.5)
    - `max_confidence`: 신뢰도 상한선 (기본: 0.95)

### 데이터 관리
- `GET /api/v1/ml/sample-datasets` - 사용 가능한 JSON 데이터셋 목록 조회
- `POST /api/v1/ml/validate-json` - JSON 데이터셋 형식 검증

### 상태 조회
- `GET /api/v1/ml/training-status` - 현재 훈련 상태 조회
- `GET /api/v1/ml/trained-models` - 훈련된 모델 목록 조회
- `GET /api/v1/ml/health` - 서비스 상태 확인

## 📊 데이터셋 구조

### JSON 데이터셋 형식
```json
[
  {
    "id": "E-POS-001",
    "text": "현대자동차 그룹이 국내 사업장 전력의 100%를 재생에너지로 전환하는 'RE100'에 가입했다.",
    "category": "E",
    "sentiment": "긍정",
    "label": "E-긍정"
  }
]
```

### 지원하는 카테고리
- **E**: 환경(Environmental)
- **S**: 사회(Social)
- **G**: 지배구조(Governance)
- **FIN**: 재무 관련 뉴스
- **기타**: 기타 카테고리

### 지원하는 감정
- **긍정**: 긍정적인 뉴스
- **부정**: 부정적인 뉴스
- **중립**: 중립적인 뉴스

## 🏷️ 모델 이름 관리

### 모델 이름 지정 규칙
1. **사용자 지정**: `model_name` 파라미터로 원하는 이름 지정
   ```json
   {
     "model_name": "esg_news_classifier_v1"
   }
   ```

2. **자동 생성**: `model_name` 미지정 시 자동 생성
   - 형식: `{파일명}_{타임스탬프}`
   - 예: `news_dataset_poc_20250619_143022`
   - 카테고리 모델: `{모델명}_category`
   - 감정 모델: `{모델명}_sentiment`

### 모델 저장 경로
- **기본 경로**: `./models/{model_name}/`
- **포함 파일들**:
  - `pytorch_model.bin` - 훈련된 모델
  - `config.json` - 모델 설정
  - `tokenizer.json` - 토크나이저
  - `label_encoder.json` - 라벨 매핑
  - `training_summary.json` - 훈련 요약
  - `confusion_matrix.png` - 혼동 행렬 시각화
  - `classification_report.csv` - 상세 성능 보고서
  - `calibration_config.json` - 신뢰도 보정 설정 (보정 적용 시)

## 🎯 사용 예시

### 1. JSON 데이터셋으로 모델 훈련하기
```bash
curl -X POST "http://localhost:8000/api/v1/ml/train-models" \
  -H "Content-Type: application/json" \
  -d '{
    "json_file_path": "news_dataset_poc.json",
    "model_name": "esg_news_model_v1",
    "apply_calibration": true,
    "temperature": 1.5,
    "max_confidence": 0.95
  }'
```

### 2. 사용 가능한 데이터셋 확인
```bash
curl -X GET "http://localhost:8000/api/v1/ml/sample-datasets"
```

### 3. JSON 데이터셋 검증
```bash
curl -X POST "http://localhost:8000/api/v1/ml/validate-json?json_file_path=news_dataset_poc.json"
```

### 4. 훈련 상태 확인
```bash
curl -X GET "http://localhost:8000/api/v1/ml/training-status"
```

### 5. 훈련된 모델 목록 조회
```bash
curl -X GET "http://localhost:8000/api/v1/ml/trained-models"
```

## 🔧 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서비스 실행
```bash
# 개발 모드
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📈 성능 최적화

### GPU 설정
- RTX 2080에 최적화된 배치 크기 및 메모리 관리
- 자동 혼합 정밀도(AMP) 지원
- 동적 배치 크기 조정

### 신뢰도 보정
- Temperature Scaling으로 과신뢰 문제 해결
- 텍스트 길이별 신뢰도 조정
- 카테고리별 임계값 최적화

## 🛠️ 기술 스택

- **프레임워크**: FastAPI
- **ML 라이브러리**: PyTorch, Transformers (Hugging Face)
- **모델**: KLUE RoBERTa Large (한국어 특화)
- **GPU 가속**: CUDA (RTX 2080 최적화)
- **데이터 처리**: Pandas, NumPy
- **시각화**: Matplotlib, Seaborn

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.