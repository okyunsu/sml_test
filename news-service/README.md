# News Service v2.0 - 통합 뉴스 분석 마이크로서비스

뉴스 검색 및 분석을 위한 현대적인 마이크로서비스입니다. 네이버 뉴스 API를 활용하여 뉴스 데이터를 수집하고, ML 서비스와 연동하여 지능형 뉴스 분석을 수행합니다.

## 🚀 v2.0 주요 업데이트

### 아키텍처 개선 (리팩터링 완료)
- **Clean Architecture 도입**: 명확한 계층 분리와 의존성 주입
- **마틴 파울러 리팩터링 적용**: 5개 서비스 완전 리팩터링
  - Extract Class: 9개의 단일 책임 클래스로 분리
  - Extract Method: 긴 메서드들을 작은 메서드로 분해
  - Strategy Pattern: ML 분석 전략 패턴 적용
  - Factory Pattern: 모델 로더 팩토리 구현
- **통합 라우터 시스템**: 사용 목적별로 분리된 API 구조
- **스마트 캐시 전략**: Redis 기반 지능형 캐싱
- **코드 품질 향상**: 43% 코드 감소, 단일 책임 원칙 적용

### 새로운 API 구조
```
/api/v1/search/                    # 🔍 스마트 검색 (캐시 우선 → 실시간)
/api/v1/dashboard/                 # 📊 대시보드 (백그라운드 데이터)
/api/v1/system/                    # 🛠️ 시스템 관리
```

## 주요 기능

### 1. 🔍 스마트 검색 시스템
- **캐시 우선 전략**: 기존 분석 결과가 있으면 즉시 반환 (100ms)
- **실시간 분석**: 캐시 없음 시 실시간 검색 및 분석 수행 (2-5초)
- **중복 제거**: 유사한 뉴스 자동 제거 (유사도 기반)
- **비동기 처리**: 고성능 비동기 검색

### 2. 📊 대시보드 시스템
- **백그라운드 모니터링**: 30분마다 자동 분석 (Redis + Celery)
- **분석 히스토리**: 과거 분석 이력 관리
- **실시간 상태**: 시스템 및 분석 상태 모니터링
- **캐시 관리**: 분석 결과 캐시 제어

### 3. 🤖 ML 기반 뉴스 분석 (리팩터링 완료)
- **ESG 분류**: Environmental, Social, Governance 카테고리 분류
- **감정 분석**: 긍정/부정/중립 감정 분석
- **키워드 추출**: 주요 키워드 자동 추출
- **전략 패턴**: ML 분석 전략 패턴 적용 (ml_strategies.py)
- **팩토리 패턴**: 모델 로더 팩토리 구현 (ml_loader.py)
- **우선순위 기반 분석**: 로컬 ML → 외부 ML → 키워드 기반 폴백
- **단일 책임 원칙**: 각 분석 기능별 독립적인 클래스 분리

### 4. ⚡ 성능 최적화
- **동시 처리**: 최대 10개의 검색 요청 동시 처리
- **연결 풀링**: HTTP 클라이언트 최적화
- **부분 실패 허용**: 일부 요청 실패 시에도 나머지 결과 반환

## 🔗 API 엔드포인트

### 🔍 스마트 검색 API

#### 1. 일반 뉴스 검색
```http
POST /api/v1/search/news
Content-Type: application/json

{
  "query": "ESG",
  "max_results": 10,
  "sort": "accuracy"
}
```

#### 2. 회사 뉴스 검색 (스마트 캐시)
```http
POST /api/v1/search/companies/삼성전자
Content-Type: application/json

{
  "max_results": 50,
  "sort": "date"
}
```

#### 3. 회사 뉴스 분석 (스마트 캐시)
```http
POST /api/v1/search/companies/삼성전자/analyze
Content-Type: application/json

{
  "max_results": 100,
  "force_refresh": false
}
```

**스마트 캐시 동작:**
1. 캐시 확인 (Redis) → 있으면 즉시 반환 ⚡
2. 캐시 없음 → 실시간 검색/분석 → 캐시 저장 → 반환 🔄

#### 4. 배치 검색
```http
POST /api/v1/search/batch
Content-Type: application/json

[
  {
    "query": "삼성전자",
    "max_results": 10
  },
  {
    "query": "LG전자", 
    "max_results": 10
  }
]
```

#### 5. 트렌딩 키워드
```http
GET /api/v1/search/trending
```

### 📊 대시보드 API

#### 1. 전체 상태 조회
```http
GET /api/v1/dashboard/status
```

#### 2. 회사 최신 분석 결과
```http
GET /api/v1/dashboard/companies/삼성전자/latest
```

#### 3. 분석 히스토리
```http
GET /api/v1/dashboard/companies/삼성전자/history?limit=10
```

#### 4. 백그라운드 분석 요청
```http
POST /api/v1/dashboard/companies/삼성전자/trigger
```

#### 5. 캐시 관리
```http
GET /api/v1/dashboard/cache/info
DELETE /api/v1/dashboard/cache/삼성전자
```

### 🛠️ 시스템 관리 API

#### 1. 헬스체크
```http
GET /api/v1/system/health
```

#### 2. 시스템 테스트
```http
GET /api/v1/system/test/integration
```

## 📋 응답 형식

### 뉴스 검색 응답
```json
{
  "search_metadata": {
    "query": "삼성전자",
    "total_found": 1247,
    "returned_count": 50,
    "cache_hit": true,
    "response_time_ms": 120
  },
  "items": [
    {
      "title": "삼성전자, ESG 경영 강화 발표",
      "url": "https://example.com/news/123",
      "summary": "삼성전자가 환경 친화적 경영 방침을 발표했다...",
      "published_date": "2024-01-15T10:30:00Z",
      "news_source": "조선비즈",
      "relevance_score": 0.95
    }
  ],
  "deduplication": {
    "original_count": 75,
    "duplicates_removed": 25,
    "similarity_threshold": 0.75
  }
}
```

### 뉴스 분석 응답
```json
{
  "analysis_metadata": {
    "company": "삼성전자",
    "analyzed_count": 50,
    "analysis_time": "2024-01-15T10:30:00Z",
    "ml_service_status": "local_model",
    "cache_hit": false
  },
  "analyzed_news": [
    {
      "title": "삼성전자, ESG 경영 강화 발표",
      "url": "https://example.com/news/123",
      "summary": "삼성전자가 환경 친화적 경영 방침을 발표했다...",
      "esg_classification": {
        "category": "E",
        "confidence": 0.95,
        "reasoning": "환경 관련 내용 포함"
      },
      "sentiment_analysis": {
        "label": "긍정",
        "confidence": 0.87,
        "scores": {
          "positive": 0.87,
          "neutral": 0.10,
          "negative": 0.03
        }
      },
      "published_date": "2024-01-15T10:30:00Z",
      "news_source": "조선비즈"
    }
  ],
  "summary": {
    "total_analyzed": 50,
    "esg_distribution": {
      "E": 20,
      "S": 15,
      "G": 10,
      "기타": 5
    },
    "sentiment_distribution": {
      "긍정": 35,
      "중립": 12,
      "부정": 3
    },
    "top_keywords": ["환경", "ESG", "지속가능경영", "친환경"]
  }
}
```

## 🏗️ 기술 스택

### 백엔드 아키텍처
- **Python 3.12**: 최신 안정 버전
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **Pydantic**: 데이터 검증 및 설정 관리
- **httpx**: 비동기 HTTP 클라이언트

### 데이터 & 캐싱
- **Redis**: 분석 결과 캐싱 및 메시지 큐
- **Celery**: 백그라운드 작업 처리
- **네이버 검색 API**: 뉴스 데이터 소스

### ML & 분석
- **Transformers**: 허깅페이스 모델 활용
- **파인튜닝 모델**: ESG 분류 및 감정 분석
- **전략 패턴**: 모델 로딩 최적화

## 🔧 주요 특징

### 1. Clean Architecture (리팩터링 완료)
```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│        (unified_router.py)              │
├─────────────────────────────────────────┤
│           Controller Layer              │
│  (news_controller, dashboard_controller)│
├─────────────────────────────────────────┤
│            Domain Layer                 │
│   Services: 비즈니스 로직 (5개 서비스)   │
│   Models: DTO & 전략 패턴 구현          │
├─────────────────────────────────────────┤
│         Infrastructure Layer            │
│  HTTP/Redis 클라이언트, ML 로더,        │
│  분석 전략 구현체, 의존성 주입          │
└─────────────────────────────────────────┘
```

**리팩터링 적용 사항:**
- **Extract Class**: 9개의 단일 책임 클래스로 분리
- **Extract Method**: 긴 메서드들을 작은 메서드로 분해  
- **Remove Duplicate Code**: 공통 컴포넌트로 중복 제거
- **Strategy Pattern**: ML 분석 전략 패턴 적용
- **Factory Pattern**: 모델 로더 팩토리 구현
- **Dependency Injection**: 의존성 주입 컨테이너 적용

### 2. 의존성 주입
- **컨테이너 기반**: dependencies.py에서 중앙 관리
- **테스트 용이성**: Mock 객체 주입 가능
- **느슨한 결합**: 인터페이스 기반 설계

### 3. 에러 처리 표준화
- **커스텀 예외**: exceptions.py에서 중앙 관리
- **HTTP 상태 코드**: 적절한 상태 코드 반환
- **상세 에러 메시지**: 디버깅 정보 포함

### 4. 설정 통합
- **환경변수 지원**: .env 파일 및 환경변수
- **타입 안전성**: Pydantic 기반 설정 검증
- **계층별 설정**: 기능별 설정 분리

## ⚙️ 설정

### 환경 변수
```bash
# .env 파일
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
MODEL_NAME=test222
LOG_LEVEL=INFO

# Redis 설정 (선택사항)
REDIS_URL=redis://localhost:6379/0

# ML 서비스 설정
ML_SERVICE_URL=http://localhost:8004
```

### Docker 실행
```bash
# 기본 CPU 환경
docker-compose -f docker-compose.cpu.yml up -d

# Redis 포함 (대시보드 기능)
docker-compose -f docker-compose.redis.yml up -d

# GPU 환경 (고성능)
docker-compose -f docker-compose.gpu.yml up -d
```

## 🚀 빠른 시작

### 1. 개발 환경 설정
```bash
# 저장소 클론
git clone <repository>
cd news-service

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### 2. API 테스트
```bash
# 헬스체크
curl http://localhost:8002/api/v1/system/health

# 간단한 뉴스 검색
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자 \
  -H "Content-Type: application/json" \
  -d '{"max_results": 10}'

# 뉴스 분석
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자/analyze \
  -H "Content-Type: application/json" \
  -d '{"max_results": 50}'
```

### 3. API 문서 확인
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## 📊 성능 지표

### 응답 시간
- **캐시 히트**: 100-200ms ⚡
- **실시간 검색**: 2-5초 🔄
- **배치 처리**: 10-30초 📦

### 리소스 사용량
- **메모리**: 2-4GB (CPU), 4-8GB (GPU)
- **CPU**: 1-2 코어 (일반), 4+ 코어 (GPU)
- **네트워크**: API 호출당 10-50KB

### 처리 용량
- **동시 요청**: 최대 10개
- **일일 처리량**: 10,000+ 뉴스 분석
- **캐시 적중률**: 70-90%

## 🔍 모니터링

### 시스템 상태
```bash
# 전체 상태 확인
curl http://localhost:8002/api/v1/dashboard/status

# 로그 확인
docker logs news-service-cpu --tail 50

# 리소스 모니터링
docker stats news-service-cpu
```

### 성능 메트릭
- **응답 시간**: API 응답 시간 추적
- **캐시 적중률**: Redis 캐시 효율성
- **에러율**: 실패한 요청 비율
- **ML 서비스 상태**: 모델 로딩 및 추론 상태

## 🛠️ 개발 가이드

### 코드 구조
```
app/
├── api/
│   └── unified_router.py          # 통합 라우터
├── core/
│   ├── dependencies.py            # 의존성 주입
│   ├── exceptions.py              # 예외 처리
│   ├── http_client.py             # HTTP 클라이언트
│   └── redis_client.py            # Redis 클라이언트
├── domain/
│   ├── controller/                # 컨트롤러 계층
│   │   ├── news_controller.py     # 뉴스 검색/분석 컨트롤러
│   │   └── dashboard_controller.py # 대시보드 컨트롤러
│   ├── service/                   # 서비스 계층 (리팩터링 완료)
│   │   ├── ml_inference_service.py     # ML 추론 서비스
│   │   ├── news_analysis_service.py    # 뉴스 분석 서비스
│   │   ├── news_service.py             # 뉴스 검색 서비스
│   │   ├── analysis_workflow_service.py # 분석 워크플로우
│   │   └── dashboard_service.py        # 대시보드 서비스
│   └── model/                     # 모델 계층 (DTO + ML 관련)
│       ├── news_dto.py            # 뉴스 데이터 전송 객체
│       ├── ml_strategies.py       # 분석 전략 패턴 구현
│       └── ml_loader.py           # ML 모델 로더
├── config/
│   ├── settings.py                # 기본 설정
│   └── ml_settings.py             # ML 설정
└── workers/                       # 백그라운드 작업 (Celery)
    ├── celery_app.py              # Celery 애플리케이션
    └── analysis_worker.py         # 분석 워커
```

### 새 기능 추가 (리팩터링된 구조)
1. **도메인 모델 정의**: `domain/model/`에 DTO 및 전략 클래스 추가
   - `news_dto.py`: 새로운 데이터 전송 객체 정의
   - `ml_strategies.py`: 새로운 분석 전략 구현
2. **서비스 로직 구현**: `domain/service/`에 비즈니스 로직 추가
   - 단일 책임 원칙에 따른 서비스 클래스 작성
   - 의존성 주입을 통한 느슨한 결합 구현
3. **컨트롤러 작성**: `domain/controller/`에 API 로직 추가
   - 서비스 계층과의 연결 담당
   - 요청/응답 변환 처리
4. **라우터 등록**: `unified_router.py`에 엔드포인트 추가
5. **인프라 컴포넌트**: `core/`에 공통 컴포넌트 추가
   - HTTP 클라이언트, Redis 클라이언트 등

### 테스트
```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# API 테스트
pytest tests/api/
```

## 📝 라이선스

MIT License

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 지원

- **Issues**: GitHub Issues 탭에서 버그 리포트 및 기능 요청
- **문서**: `/docs` 엔드포인트에서 상세 API 문서 확인
- **로그**: Docker 로그에서 실시간 상태 확인