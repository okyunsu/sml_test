# SASB-based ESG Analysis Service

SASB(Sustainability Accounting Standards Board) 프레임워크 기반의 ESG 뉴스 분석 서비스입니다.

## 🚀 주요 기능

### 🎯 핵심 분석 기능
- **조합 키워드 시스템**: (산업 키워드) AND (SASB 이슈 키워드) 조합으로 정확도 높은 뉴스 수집
- **ML 모델 기반 감성 분석**: Hugging Face Transformers 모델을 사용한 정교한 감성 평가
- **회사별 SASB 분석**: 특정 회사와 SASB 키워드 조합 분석
- **실시간 및 백그라운드 분석**: 즉시 분석과 Worker 백그라운드 처리 모두 지원

### 🔄 백그라운드 시스템
- **Celery Worker**: 자동화된 백그라운드 뉴스 수집 및 분석
- **최적화된 스케줄링**: 30분 간격의 효율적인 작업 스케줄
- **Redis 캐싱**: 고성능 데이터 캐시 및 Worker 결과 저장

### 📊 모니터링 & 관리
- **실시간 대시보드**: 시스템 상태 및 분석 결과 모니터링
- **Worker 상태 조회**: 백그라운드 작업 진행 상황 확인
- **캐시 관리**: Redis 캐시 상태 조회 및 관리

## 🎯 조합 키워드 시스템

### 검색 정확도 개선
기존의 단일 키워드 검색에서 **이중 조합 키워드 시스템**으로 전환하여 관련성 높은 뉴스만 수집:

**기존 문제**: `탄소중립` → 골프장, 정부기관, 박물관 등 비관련 뉴스 포함
**개선 후**: `(신재생에너지 OR 발전소) AND 탄소중립` → 신재생에너지 산업 뉴스만

### 키워드 그룹
- **산업 키워드 (33개)**: 신재생에너지, 태양광, 풍력, 발전소, ESS, 수소 등
- **SASB 이슈 키워드 (53개)**: 탄소중립, 온실가스, 폐패널, SMP, 중대재해 등

## 🤖 ML 모델 기반 감성 분석

### 고도화된 감성 평가
- **프레임워크**: Hugging Face Transformers (PyTorch)
- **모델**: `newstun-service`에서 훈련된 한국어 특화 감성 분석 모델
- **출력**: 3-class 분류 (긍정/부정/중립) + 신뢰도 점수
- **정확도**: 키워드 매핑 대비 문맥 이해 기반 정교한 분석

### 감성 라벨 매핑
```
LABEL_0 → 긍정 (positive)
LABEL_1 → 부정 (negative)  
LABEL_2 → 중립 (neutral)
```

## 📅 Worker 스케줄링

### 개발 친화적 실행 주기
- **조합 키워드 분석**: 시작 후 1분, 이후 10분마다 (1,11,21,31,41,51분)
- **회사별 조합 분석**: 시작 후 3분, 이후 10분마다 (3,13,23,33,43,53분)

### 빠른 개발 환경
- 서비스 시작 후 **1분 내에 첫 번째 작업** 실행
- 10분 간격으로 자주 실행되어 빠른 피드백 제공
- 시스템 부하 감소 및 유지보수 간소화

## 빠른 시작

### 1. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 환경 변수들을 설정하세요:

```bash
# 필수 설정 (Naver News API)
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Redis 설정 (기본값 사용 가능)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ML 모델 설정 (newstun-service 모델 경로)
MODEL_BASE_PATH=/app/models
MODEL_NAME=test222
DISABLE_ML_MODEL=false

# Docker 네트워크 설정
REDIS_URL=redis://redis:6379/0
```

### 2. Docker로 실행

```bash
# 전체 시스템 실행 (권장)
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f sasb-service
```

### 3. 서비스 확인

```bash
# 헬스체크
curl http://localhost:8003/health

# Worker 상태 확인
curl http://localhost:8003/api/v1/workers/status

# API 문서 확인
# http://localhost:8003/docs
```

## 📡 API 엔드포인트

### 🎨 프론트엔드 핵심 API

```bash
# 회사 + SASB 키워드 조합 분석
POST /api/v1/analyze/company-sasb
  ?company_name=두산퓨얼셀
  &sasb_keywords[]=탄소중립&sasb_keywords[]=온실가스
  &max_results=10

# SASB 키워드 전용 분석  
POST /api/v1/analyze/sasb-only
  ?sasb_keywords[]=탄소중립&sasb_keywords[]=재생에너지
  &max_results=20

# 서비스 상태 확인
GET /api/v1/health
```

### 📊 대시보드 API

```bash
# 시스템 전체 상태
GET /api/v1/dashboard/status

# SASB 뉴스 분석 결과 (Worker 결과 우선)
GET /api/v1/dashboard/sasb-news?max_results=20&force_realtime=false

# 모니터링 회사 목록
GET /api/v1/dashboard/companies

# 회사별 최신 분석 결과
GET /api/v1/dashboard/companies/{company}/latest
```

### 🔄 Worker 모니터링 API

```bash
# Worker 전체 상태
GET /api/v1/workers/status

# Worker 처리 SASB 뉴스 결과
GET /api/v1/workers/results/sasb-news?max_results=20

# 🎯 조합 키워드 검색 결과 (고정확도)
GET /api/v1/workers/results/combined-keywords?max_results=20

# 회사별 조합 키워드 검색 결과
GET /api/v1/workers/results/company-combined/{company}?max_results=20

# Worker 스케줄 정보
GET /api/v1/workers/schedule
```

### 🗄️ 캐시 관리 API

```bash
# 캐시 정보 조회
GET /api/v1/cache/info

# 회사별 캐시 삭제
DELETE /api/v1/cache/company/{company}
```

## 🏗️ 프로젝트 구조

```
sasb-service/
├── app/
│   ├── api/
│   │   └── unified_router.py       # 통합 API 라우터 (5개 라우터 통합)
│   ├── config/
│   │   └── settings.py             # 환경변수 및 설정 관리
│   ├── core/
│   │   ├── dependencies.py         # 의존성 주입 컨테이너
│   │   ├── exceptions.py           # 커스텀 예외 처리
│   │   ├── http_client.py          # HTTP 클라이언트 (Naver API)
│   │   └── redis_client.py         # Redis 클라이언트
│   ├── domain/
│   │   ├── controller/             # 컨트롤러 계층
│   │   │   ├── sasb_controller.py     # SASB 분석 컨트롤러
│   │   │   └── dashboard_controller.py # 대시보드 컨트롤러
│   │   ├── model/                  # 데이터 모델 & DTO
│   │   │   └── sasb_dto.py            # SASB 분석 데이터 모델
│   │   └── service/                # 비즈니스 로직 계층
│   │       ├── sasb_service.py        # SASB 고수준 서비스
│   │       ├── analysis_service.py    # 뉴스 분석 오케스트레이터
│   │       ├── naver_news_service.py  # 네이버 뉴스 수집
│   │       └── ml_inference_service.py # ML 모델 추론
│   ├── workers/                    # Celery 백그라운드 시스템
│   │   ├── celery_app.py              # Celery 앱 & 스케줄 설정
│   │   └── analysis_worker.py         # 조합 키워드 분석 워커
│   └── main.py                     # FastAPI 애플리케이션 진입점
├── Dockerfile                      # 컨테이너 이미지 빌드
├── docker-compose.yml              # 서비스 오케스트레이션
├── requirements.txt                # Python 의존성
└── README.md                       # 프로젝트 문서
```

## 🛠️ 개발 가이드

### 로컬 개발 환경

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
cp .env.example .env

# 애플리케이션 실행
python -m app.main
```

### Celery Worker 개발

```bash
# Worker 실행 (분석 작업 처리)
celery -A app.workers.celery_app worker --loglevel=info

# Beat 스케줄러 실행 (별도 터미널)
celery -A app.workers.celery_app beat --loglevel=info

# Worker 모니터링
celery -A app.workers.celery_app flower
```

### 테스트 및 디버깅

```bash
# 특정 Worker 태스크 수동 실행
python -c "
from app.workers.analysis_worker import run_combined_keywords_analysis
run_combined_keywords_analysis.delay()
"

# Redis 데이터 확인
redis-cli
> keys latest_*
> get latest_combined_keywords_analysis
```

## 🔍 성능 최적화

### 검색 정확도 향상
- **기존 방식**: 단일 키워드 → 관련성 낮은 다량의 뉴스
- **개선 방식**: 조합 키워드 → 관련성 높은 정제된 뉴스
- **결과**: 볼륨 감소, 품질 대폭 향상

### 응답 속도 최적화
- **Worker 우선 전략**: 사전 처리된 Worker 결과 우선 반환
- **Redis 캐싱**: 실시간 분석 결과 30-60분 캐시
- **백그라운드 처리**: 사용자 대기 시간 제거

### 시스템 효율성
- **스케줄 단순화**: 5개 → 2개 스케줄로 부하 감소
- **메모리 최적화**: ML 모델 한 번 로딩 후 재사용
- **병렬 처리**: 다중 키워드 조합 동시 처리

## 🚨 문제 해결

### 일반적인 문제들

#### 1. Redis 연결 오류
```bash
# Redis 상태 확인
docker-compose ps redis

# Redis 연결 테스트
redis-cli ping
# 응답: PONG
```

#### 2. Worker 작업 실패
```bash
# Worker 로그 확인
docker-compose logs celery-worker

# Worker 상태 API 확인
curl http://localhost:8003/api/v1/workers/status
```

#### 3. ML 모델 로딩 오류
```bash
# 모델 없이 실행 (키워드 기반 감성 분석)
DISABLE_ML_MODEL=true docker-compose up

# 모델 경로 확인
docker-compose exec sasb-service ls -la /app/models/
```

#### 4. Naver API 오류
```bash
# API 키 확인
echo $NAVER_CLIENT_ID
echo $NAVER_CLIENT_SECRET

# API 호출 테스트
curl -H "X-Naver-Client-Id: YOUR_ID" \
     -H "X-Naver-Client-Secret: YOUR_SECRET" \
     "https://openapi.naver.com/v1/search/news.json?query=테스트"
```

### 성능 튜닝

#### Redis 메모리 최적화
```bash
# Redis 메모리 사용량 확인
redis-cli info memory

# 만료된 키 정리
redis-cli --scan --pattern "expired:*" | xargs redis-cli del
```

#### Worker 처리량 조정
```bash
# Worker 동시 처리 수 증가
celery -A app.workers.celery_app worker --concurrency=4

# 메모리 기반 동적 조정
celery -A app.workers.celery_app worker --autoscale=10,3
```

## 📈 모니터링 & 로깅

### 로그 확인
```bash
# 실시간 로그 모니터링
docker-compose logs -f sasb-service

# 특정 서비스 로그
docker-compose logs celery-worker
docker-compose logs redis

# 에러 로그만 필터링
docker-compose logs sasb-service | grep ERROR
```

### 시스템 상태 모니터링
```bash
# 전체 시스템 상태
curl http://localhost:8003/api/v1/dashboard/status | jq

# Worker 상태 모니터링
curl http://localhost:8003/api/v1/workers/status | jq

# 캐시 상태 확인  
curl http://localhost:8003/api/v1/cache/info | jq
```

## 🔗 관련 서비스

이 서비스는 다음 서비스들과 연동됩니다:

- **newstun-service**: ML 모델 훈련 및 제공
- **news-service**: 뉴스 수집 및 분석 (유사 아키텍처)
- **gateway**: API 게이트웨이 및 인증

## 📄 라이선스

[MIT License](LICENSE)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**SASB Analysis Service** - ESG 뉴스 분석의 새로운 표준 🚀 