# News Service - Redis 기반 자동 대시보드

기존 News Service에 **Redis + Celery Worker**를 추가하여 **30분마다 자동으로 삼성전자, LG전자 뉴스를 분석**하고 대시보드에서 확인할 수 있는 기능을 구현했습니다.

## 🚀 주요 기능

### 1. 자동 뉴스 분석
- **30분마다 자동 실행**: 삼성전자, LG전자 뉴스 분석
- **백그라운드 처리**: 메인 API 성능에 영향 없음
- **Redis 캐싱**: 분석 결과를 24시간 캐시
- **분석 히스토리**: 과거 분석 이력 최대 50개 보관

### 2. 대시보드 API
- **실시간 상태 조회**: 현재 분석 상태 및 Redis 연결 상태
- **회사별 분석 결과**: 최신 분석 결과 및 히스토리 조회
- **수동 분석 요청**: 즉시 분석이 필요한 경우 백그라운드 실행
- **캐시 관리**: 캐시 정보 조회 및 삭제

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   News API      │    │  Celery Worker  │    │  Celery Beat    │
│  (FastAPI)      │    │ (뉴스 분석)     │    │ (30분 스케줄)   │
│  Port: 8002     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │  (메시지큐+캐시) │
                    │   Port: 6379    │
                    └─────────────────┘
```

## 📡 새로운 API 엔드포인트

### 대시보드 상태 관리

#### 1. 전체 상태 조회
```http
GET /api/v1/dashboard/status
```
**응답 예시:**
```json
{
  "status": "running",
  "redis_connected": true,
  "monitored_companies": ["삼성전자", "LG전자"],
  "last_analysis_at": "2024-01-15T10:30:00",
  "total_success": 2,
  "total_error": 0
}
```

#### 2. 모니터링 회사 목록
```http
GET /api/v1/dashboard/companies
```

### 분석 결과 조회

#### 3. 특정 회사 최신 분석 결과
```http
GET /api/v1/dashboard/analysis/삼성전자
```

#### 4. 특정 회사 분석 히스토리
```http
GET /api/v1/dashboard/analysis/삼성전자/history?limit=10
```

#### 5. 모든 회사 최신 분석 결과
```http
GET /api/v1/dashboard/latest
```

### 수동 제어

#### 6. 특정 회사 수동 분석 요청
```http
POST /api/v1/dashboard/analyze/삼성전자
```

#### 7. 캐시 정보 조회
```http
GET /api/v1/dashboard/cache/info
```

#### 8. 특정 회사 캐시 삭제
```http
DELETE /api/v1/dashboard/cache/삼성전자
```

## 🐳 실행 방법

### 1. Redis 포함 전체 서비스 실행
```bash
# Redis + News Service + Celery Worker + Beat 모두 실행
docker-compose -f docker-compose.redis.yml up -d

# 로그 확인
docker-compose -f docker-compose.redis.yml logs -f
```

### 2. 개별 서비스 실행 (개발 환경)
```bash
# 1단계: Redis 실행
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 2단계: News Service 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# 3단계: Celery Worker 실행 (별도 터미널)
celery -A app.workers.celery_app worker --loglevel=info

# 4단계: Celery Beat 실행 (별도 터미널)
celery -A app.workers.celery_app beat --loglevel=info
```

## 📊 대시보드 확인 방법

### 1. Swagger UI에서 테스트
```
http://localhost:8002/docs
```
- `/api/v1/dashboard/*` 엔드포인트들을 직접 테스트 가능

### 2. 분석 상태 모니터링
```bash
# 전체 상태 확인
curl http://localhost:8002/api/v1/dashboard/status

# 삼성전자 최신 분석 결과 확인
curl http://localhost:8002/api/v1/dashboard/analysis/삼성전자

# 모든 회사 최신 결과 확인
curl http://localhost:8002/api/v1/dashboard/latest
```

### 3. 수동 분석 실행
```bash
# 삼성전자 즉시 분석 (백그라운드)
curl -X POST http://localhost:8002/api/v1/dashboard/analyze/삼성전자
```

## ⚙️ 설정

### 환경 변수
```bash
# .env 파일 또는 환경 변수 설정
REDIS_URL=redis://localhost:6379/0
MODEL_NAME=test123
```

### 분석 주기 변경
`app/workers/celery_app.py`에서 스케줄 변경 가능:
```python
# 30분마다 → 15분마다 변경
"schedule": crontab(minute="*/15"),

# 매 시간 정각 → 30분마다 변경  
"schedule": crontab(minute="*/30"),
```

### 분석 대상 회사 변경
`app/api/dashboard_router.py`에서 회사 목록 변경:
```python
MONITORED_COMPANIES = ["삼성전자", "LG전자", "SK하이닉스"]
```

## 🔍 트러블슈팅

### 1. Redis 연결 오류
```bash
# Redis 상태 확인
docker ps | grep redis
redis-cli ping
```

### 2. Celery 작업 확인
```bash
# 활성 작업 확인
celery -A app.workers.celery_app inspect active

# 등록된 작업 확인
celery -A app.workers.celery_app inspect registered
```

### 3. 분석 결과가 없는 경우
- 첫 실행 후 30분 대기 (자동 분석)
- 또는 수동 분석 실행: `POST /api/v1/dashboard/analyze/{company}`

## 📈 성능 최적화

- **메모리 사용량**: Worker 1.5GB, Beat 256MB로 제한
- **CPU 사용량**: Worker 1코어, Beat 0.5코어로 제한
- **캐시 만료**: 분석 결과 24시간, 히스토리 7일
- **동시성**: Worker 2개 프로세스로 동시 처리

## 🔄 다음 단계

프론트엔드에서 이 API들을 활용하여:
1. **실시간 대시보드** 구현
2. **차트/그래프** 시각화
3. **WebSocket 연결** (추가 개발 필요)
4. **알림 기능** (이메일/슬랙 등) 