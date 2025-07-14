# SASB-based ESG Analysis Service

SASB(Sustainability Accounting Standards Board) 프레임워크 기반의 ESG 뉴스 분석 서비스입니다.

## 주요 기능

- 회사별 SASB 키워드 기반 뉴스 수집 및 감성 분석
- SASB 키워드 전용 뉴스 분석
- 실시간 대시보드 및 캐시 관리
- Celery 기반 백그라운드 작업 스케줄링
- Redis 기반 데이터 캐싱

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

# ML 모델 설정 (선택사항)
MODEL_BASE_PATH=/app/models
MODEL_NAME=your_model_name
DISABLE_ML_MODEL=false
```

### 2. Docker로 실행

```bash
# 단일 서비스 실행
docker-compose up --build

# 전체 시스템 실행 (Redis 포함)
docker-compose -f docker-compose.yml up --build
```

### 3. 서비스 확인

```bash
# 헬스체크
curl http://localhost:8003/health

# API 문서 확인
# http://localhost:8003/docs
```

## API 엔드포인트

### 프론트엔드 API

- `POST /api/v1/analyze/company-sasb` - 회사 + SASB 키워드 뉴스 분석
- `POST /api/v1/analyze/sasb-only` - SASB 키워드 전용 뉴스 분석
- `GET /api/v1/health` - 서비스 상태 확인

### 대시보드 API

- `GET /dashboard/status` - 전체 시스템 상태
- `GET /dashboard/companies` - 모니터링 중인 회사 목록
- `GET /dashboard/companies/{company}/latest` - 회사별 최신 분석 결과

### 캐시 관리 API

- `GET /cache/info` - 캐시 정보 조회
- `DELETE /cache/company/{company}` - 회사별 캐시 삭제

## 프로젝트 구조

```
sasb-service/
├── app/
│   ├── api/
│   │   └── unified_router.py       # 통합 API 라우터
│   ├── config/
│   │   └── settings.py             # 설정 관리
│   ├── core/
│   │   ├── dependencies.py         # 의존성 주입
│   │   ├── exceptions.py           # 예외 처리
│   │   ├── http_client.py          # HTTP 클라이언트
│   │   └── redis_client.py         # Redis 클라이언트
│   ├── domain/
│   │   ├── controller/             # 컨트롤러 계층
│   │   │   ├── sasb_controller.py
│   │   │   └── dashboard_controller.py
│   │   ├── model/                  # 데이터 모델
│   │   │   └── sasb_dto.py
│   │   └── service/                # 서비스 계층
│   │       ├── sasb_service.py
│   │       ├── analysis_service.py
│   │       ├── naver_news_service.py
│   │       └── ml_inference_service.py
│   ├── workers/                    # Celery 워커
│   │   ├── celery_app.py
│   │   └── analysis_worker.py
│   └── main.py                     # 애플리케이션 진입점
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 개발 가이드

### 로컬 개발 환경

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
python -m app.main
```

### Celery 워커 실행

```bash
# 워커 실행
celery -A app.workers.celery_app worker --loglevel=info

# Beat 스케줄러 실행 (별도 터미널)
celery -A app.workers.celery_app beat --loglevel=info
```

## 문제 해결

### 일반적인 문제들

1. **Redis 연결 오류**
   - Redis가 실행 중인지 확인
   - `CELERY_BROKER_URL` 설정 확인

2. **Naver API 오류**
   - `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 확인
   - API 호출 한도 확인

3. **ML 모델 로딩 오류**
   - `DISABLE_ML_MODEL=true`로 설정하여 모델 없이 실행
   - 모델 경로 및 파일 확인

### 로그 확인

```bash
# 컨테이너 로그 확인
docker-compose logs sasb-service

# 실시간 로그 모니터링
docker-compose logs -f sasb-service
``` 