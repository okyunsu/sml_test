# News Service v2.0 - Redis 기반 자동 대시보드

v2.0에서는 기존 News Service에 **통합 라우터 시스템**과 **스마트 캐시 전략**이 추가되어, **Redis + Celery Worker**를 통한 **30분마다 자동 뉴스 분석** 및 **지능형 대시보드** 기능을 제공합니다.

## 🚀 v2.0 주요 기능

### 1. 📊 스마트 대시보드 시스템
- **30분마다 자동 실행**: 삼성전자, LG전자 뉴스 분석
- **백그라운드 처리**: 메인 API 성능에 영향 없음
- **Redis 캐싱**: 분석 결과를 24시간 캐시
- **분석 히스토리**: 과거 분석 이력 최대 50개 보관
- **실시간 상태 모니터링**: 시스템 전체 상태 추적

### 2. 🔍 스마트 캐시 전략
- **캐시 우선 조회**: 기존 분석 결과가 있으면 즉시 반환 (100ms)
- **실시간 대체**: 캐시 없음 시 실시간 검색/분석 수행 (2-5초)
- **지능형 만료**: 분석 결과 24시간, 히스토리 7일 자동 관리
- **강제 새로고침**: `force_refresh` 옵션으로 캐시 무시 가능

### 3. 🏗️ 통합 라우터 아키텍처 (리팩터링 완료)
- **Clean Architecture**: 계층별 명확한 분리 (Presentation → Controller → Service → Infrastructure)
- **마틴 파울러 리팩터링 적용**: 5개 서비스 완전 리팩터링
  - Extract Class: 9개의 단일 책임 클래스로 분리
  - Extract Method: 긴 메서드들을 작은 메서드로 분해
  - Strategy Pattern: ML 분석 전략 패턴 적용
  - Factory Pattern: 모델 로더 팩토리 구현
- **의존성 주입**: 테스트 가능한 모듈화 구조
- **에러 처리 표준화**: 일관된 예외 처리 시스템
- **성능 최적화**: 43% 코드 감소, 응답 시간 개선

## 🏗️ v2.0 아키텍처 (리팩터링 완료)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Unified Router │    │  Celery Worker  │    │  Celery Beat    │
│ (통합 라우터)   │    │ (뉴스 분석)     │    │ (30분 스케줄)   │
│  Port: 8002     │    │                 │    │                 │
│                 │    │ 🔍 Smart Search │    │ ⏰ Auto Trigger │
│ 📊 Dashboard    │    │ 🤖 ML Analysis │    │ 📅 Schedule Mgmt│
│ 🔍 Search       │    │ 💾 Cache Store  │    │                 │
│ 🛠️ System       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │ (메시지큐+캐시) │
                    │   Port: 6379    │
                    │                 │
                    │ 🔄 Message Queue│
                    │ 💾 Result Cache │
                    │ 📊 History Store│
                    └─────────────────┘

🏗️ Clean Architecture 적용 (리팩터링):
┌─────────────────────────────────────────┐
│         Presentation Layer              │ unified_router.py
├─────────────────────────────────────────┤
│         Controller Layer                │ news_controller, dashboard_controller
├─────────────────────────────────────────┤
│         Domain Layer (리팩터링 완료)     │
│  ✅ 5개 서비스: ml_inference, news_     │
│     analysis, news, workflow, dashboard │
│  ✅ 전략 패턴: ml_strategies.py         │
│  ✅ 팩토리 패턴: ml_loader.py           │
├─────────────────────────────────────────┤
│         Infrastructure Layer            │ http_client, redis_client, dependencies
└─────────────────────────────────────────┘
```

## 📡 v2.0 대시보드 API 엔드포인트

### 🏠 대시보드 상태 관리

#### 1. 전체 상태 조회
```http
GET /api/v1/dashboard/status
```
**응답 예시:**
```json
{
  "status": "running",
  "version": "2.0",
  "redis_connected": true,
  "cache_enabled": true,
  "monitored_companies": ["삼성전자", "LG전자"],
  "last_analysis_at": "2024-01-15T10:30:00",
  "total_success": 2,
  "total_error": 0,
  "performance": {
    "cache_hit_rate": "85%",
    "avg_response_time_ms": 120
  }
}
```

#### 2. 모니터링 회사 목록
```http
GET /api/v1/dashboard/companies
```

### 🔍 분석 결과 조회

#### 3. 특정 회사 최신 분석 결과
```http
GET /api/v1/dashboard/companies/삼성전자/latest
```
**응답 예시:**
```json
{
  "company": "삼성전자", 
  "analysis_metadata": {
    "analyzed_count": 50,
    "analysis_time": "2024-01-15T10:30:00Z",
    "cache_hit": true,
    "response_time_ms": 120
  },
  "summary": {
    "total_analyzed": 50,
    "esg_distribution": {"E": 20, "S": 15, "G": 10, "기타": 5},
    "sentiment_distribution": {"긍정": 35, "중립": 12, "부정": 3},
    "top_keywords": ["환경", "ESG", "지속가능경영"]
  }
}
```

#### 4. 특정 회사 분석 히스토리
```http
GET /api/v1/dashboard/companies/삼성전자/history?limit=10
```

#### 5. 모든 회사 최신 분석 결과
```http
GET /api/v1/dashboard/latest
```

### 🔧 수동 제어

#### 6. 특정 회사 백그라운드 분석 요청
```http
POST /api/v1/dashboard/companies/삼성전자/trigger
```
**응답 예시:**
```json
{
  "message": "백그라운드 분석이 요청되었습니다",
  "company": "삼성전자",
  "task_id": "abc123-def456",
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

### 💾 캐시 관리

#### 7. 캐시 전체 정보 조회
```http
GET /api/v1/dashboard/cache/info
```
**응답 예시:**
```json
{
  "total_cached_companies": 5,
  "cache_size_mb": 125.3,
  "hit_rate_24h": "87%",
  "companies": [
    {
      "company": "삼성전자",
      "last_cached": "2024-01-15T10:30:00Z",
      "cache_size_kb": 45.2,
      "hit_count": 23
    }
  ]
}
```

#### 8. 특정 회사 캐시 삭제
```http
DELETE /api/v1/dashboard/cache/삼성전자
```

#### 9. 전체 캐시 정리
```http
DELETE /api/v1/dashboard/cache/all
```

## 🔍 v2.0 스마트 검색 연동

### 캐시 우선 검색
```http
POST /api/v1/search/companies/삼성전자/analyze
Content-Type: application/json

{
  "max_results": 50,
  "force_refresh": false
}
```

**스마트 캐시 동작 흐름:**
1. 🔍 **캐시 확인** → Redis에서 기존 분석 결과 조회
2. ⚡ **캐시 히트** → 즉시 반환 (100-200ms)
3. 🔄 **캐시 미스** → 실시간 분석 수행 → 캐시 저장 → 반환 (2-5초)
4. 💾 **자동 저장** → 결과를 Redis에 24시간 캐시

## 🐳 v2.0 실행 방법

### 1. Redis 포함 전체 서비스 실행 (권장)
```bash
# v2.0 통합 시스템 - Redis + News Service + Celery Worker + Beat
docker-compose -f docker-compose.redis.yml up -d

# 로그 확인 (통합 라우터 시스템)
docker-compose -f docker-compose.redis.yml logs -f

# 특정 서비스 로그만 확인
docker-compose -f docker-compose.redis.yml logs -f news-service
docker-compose -f docker-compose.redis.yml logs -f celery-worker
docker-compose -f docker-compose.redis.yml logs -f redis
```

### 2. 개별 서비스 실행 (개발 환경)
```bash
# 1단계: Redis 실행
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 2단계: News Service v2.0 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# 3단계: Celery Worker 실행 (별도 터미널)
celery -A app.workers.celery_app worker --loglevel=info

# 4단계: Celery Beat 실행 (별도 터미널)
celery -A app.workers.celery_app beat --loglevel=info
```

## 📊 v2.0 대시보드 확인 방법

### 1. Swagger UI에서 테스트
```
http://localhost:8002/docs
```
- `/api/v1/dashboard/*` 엔드포인트들을 직접 테스트 가능
- `/api/v1/search/*` 스마트 검색 API 테스트 가능
- `/api/v1/system/*` 시스템 관리 API 테스트 가능

### 2. 분석 상태 모니터링 (v2.0)
```bash
# 전체 상태 확인
curl http://localhost:8002/api/v1/dashboard/status

# 삼성전자 최신 분석 결과 확인 (스마트 캐시)
curl http://localhost:8002/api/v1/dashboard/companies/삼성전자/latest

# 모든 회사 최신 결과 확인
curl http://localhost:8002/api/v1/dashboard/latest

# 캐시 정보 확인
curl http://localhost:8002/api/v1/dashboard/cache/info
```

### 3. 스마트 검색 테스트
```bash
# 캐시 우선 검색 (PowerShell)
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/search/companies/삼성전자/analyze" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"max_results": 50, "force_refresh": false}' |
  Select-Object -ExpandProperty Content

# 강제 새로고침 (Linux/Mac/WSL)
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자/analyze \
  -H "Content-Type: application/json" \
  -d '{"max_results": 50, "force_refresh": true}'
```

### 4. 수동 분석 실행
```bash
# 삼성전자 즉시 분석 (백그라운드)
curl -X POST http://localhost:8002/api/v1/dashboard/companies/삼성전자/trigger

# 분석 상태 확인 (몇 분 후)
curl http://localhost:8002/api/v1/dashboard/companies/삼성전자/latest
```

## ⚙️ v2.0 설정

### 환경 변수
```bash
# .env 파일 또는 환경 변수 설정
REDIS_URL=redis://localhost:6379/0
MODEL_NAME=test222
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret

# v2.0 추가 설정
LOG_LEVEL=INFO
CACHE_ENABLED=true
CACHE_TTL_HOURS=24
```

### 분석 주기 변경
`app/workers/celery_app.py`에서 스케줄 변경 가능:
```python
# 30분마다 → 15분마다 변경
"schedule": crontab(minute="*/15"),

# 매 시간 정각 → 30분마다 변경  
"schedule": crontab(minute="*/30"),

# 매일 오전 9시
"schedule": crontab(hour=9, minute=0),
```

### 분석 대상 회사 변경
`app/domain/controller/dashboard_controller.py`에서 회사 목록 변경:
```python
MONITORED_COMPANIES = ["삼성전자", "LG전자", "SK하이닉스", "카카오", "네이버"]
```

### 캐시 설정 조정
`app/config/settings.py`에서 캐시 관련 설정:
```python
CACHE_TTL_HOURS = 24      # 캐시 유지 시간
HISTORY_MAX_COUNT = 50    # 최대 히스토리 개수
CACHE_KEY_PREFIX = "news_analysis"  # 캐시 키 접두사
```

## 🔍 v2.0 트러블슈팅

### 1. 통합 라우터 관련 문제

#### API 엔드포인트 404 오류
**증상**: 기존 엔드포인트 호출 시 404 오류  
**해결**: v2.0 새로운 API 구조 사용
```bash
# ❌ 구 버전 (더 이상 작동하지 않음)
curl http://localhost:8002/api/v1/news/company/simple/analyze

# ✅ v2.0 새 버전 (스마트 캐시)
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자/analyze
```

#### 대시보드 API 접근 불가
**증상**: 대시보드 엔드포인트 호출 실패  
**해결**: Redis 환경에서 실행 확인
```bash
# Redis 포함 환경으로 실행
docker-compose -f docker-compose.redis.yml up -d

# 대시보드 상태 확인
curl http://localhost:8002/api/v1/dashboard/status
```

### 2. Redis 연결 오류
```bash
# Redis 상태 확인
docker ps | grep redis
redis-cli ping

# Redis 서비스 재시작
docker-compose -f docker-compose.redis.yml restart redis

# Redis 로그 확인
docker-compose -f docker-compose.redis.yml logs redis
```

### 3. 캐시 관련 문제

#### 캐시가 작동하지 않음
**증상**: 항상 `cache_hit: false`로 응답  
**해결 방법**:
```bash
# 1. Redis 연결 상태 확인
curl http://localhost:8002/api/v1/dashboard/status

# 2. 캐시 정보 확인
curl http://localhost:8002/api/v1/dashboard/cache/info

# 3. 캐시 수동 생성 (분석 실행)
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자/analyze \
  -H "Content-Type: application/json" \
  -d '{"max_results": 10}'
```

#### 캐시 데이터 손상
**증상**: 캐시에서 잘못된 데이터 반환  
**해결 방법**:
```bash
# 특정 회사 캐시 삭제
curl -X DELETE http://localhost:8002/api/v1/dashboard/cache/삼성전자

# 전체 캐시 정리
curl -X DELETE http://localhost:8002/api/v1/dashboard/cache/all

# 새로 분석 실행
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자/analyze \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": true}'
```

### 4. Celery 작업 확인
```bash
# 활성 작업 확인
celery -A app.workers.celery_app inspect active

# 등록된 작업 확인
celery -A app.workers.celery_app inspect registered

# 대기 중인 작업 확인
celery -A app.workers.celery_app inspect reserved

# Celery Worker 상태 확인
docker-compose -f docker-compose.redis.yml logs celery-worker
```

### 5. 분석 결과가 없는 경우
**원인**: 첫 실행 후 아직 자동 분석이 실행되지 않음  
**해결 방법**:
- 자동 분석 대기 (30분)
- 또는 수동 분석 실행: `POST /api/v1/dashboard/companies/{company}/trigger`
- 또는 직접 검색 실행: `POST /api/v1/search/companies/{company}/analyze`

### 6. 성능 관련 문제

#### 응답 시간 느림
**해결 방법**:
```bash
# 1. 캐시 적중률 확인
curl http://localhost:8002/api/v1/dashboard/cache/info

# 2. 리소스 사용량 확인
docker stats

# 3. Redis 메모리 사용량 확인
redis-cli info memory
```

#### 메모리 부족
**해결 방법**:
```yaml
# docker-compose.redis.yml에서 메모리 제한 조정
deploy:
  resources:
    limits:
      memory: 8G  # 필요에 따라 증가
```

## 📈 v2.0 성능 최적화

### 캐시 최적화
- **캐시 적중률**: 70-90% 목표
- **캐시 키 관리**: 효율적인 키 네이밍 전략
- **메모리 사용량**: Redis 메모리 모니터링
- **TTL 관리**: 자동 만료 및 정리

### 리소스 사용량 (v2.0)
- **News Service**: CPU 1-2코어, 메모리 2-3GB
- **Celery Worker**: CPU 1코어, 메모리 1.5GB
- **Celery Beat**: CPU 0.5코어, 메모리 256MB
- **Redis**: CPU 0.5코어, 메모리 512MB-2GB

### 동시성 처리
- **Worker 프로세스**: 2개 동시 실행
- **배치 크기**: 뉴스 50개씩 처리
- **큐 관리**: 우선순위 기반 작업 스케줄링

## 🔄 v2.0 다음 단계

### ✅ 완료된 리팩터링 작업
1. **Clean Architecture 적용 완료**
   - 5개 서비스 완전 리팩터링 (438줄 → 50-100줄/클래스)
   - Extract Class: 9개의 단일 책임 클래스 분리
   - Extract Method: 긴 메서드들을 작은 메서드로 분해
   - Strategy Pattern: ML 분석 전략 패턴 적용
   - Factory Pattern: 모델 로더 팩토리 구현
2. **의존성 주입 시스템 구축**
   - 테스트 가능한 모듈화 구조
   - 느슨한 결합 달성
3. **코드 품질 개선**
   - 단일 책임 원칙 준수
   - 재사용 가능한 컴포넌트 구조

### 프론트엔드 연동
1. **실시간 대시보드** 구현
   - 캐시 적중률 실시간 모니터링
   - 분석 상태 실시간 업데이트
2. **차트/그래프** 시각화
   - ESG 분포 차트
   - 감정 분석 트렌드
3. **WebSocket 연결** (추가 개발 필요)
   - 실시간 알림 시스템
4. **알림 기능** (이메일/슬랙 등)
   - 분석 완료 알림
   - 에러 발생 알림

### API 확장
1. **비교 분석**: 여러 회사 간 비교
2. **트렌드 분석**: 시간별 변화 추세
3. **키워드 분석**: 특정 키워드 기반 분석
4. **사용자 정의**: 맞춤형 분석 설정

### 모니터링 강화
1. **메트릭 수집**: Prometheus + Grafana
2. **로그 중앙화**: ELK Stack 연동
3. **알림 시스템**: 시스템 상태 모니터링
4. **성능 최적화**: 병목 지점 식별 및 개선 