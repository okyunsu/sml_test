# 🗞️ News Analysis System - 전체 프로젝트 가이드

## 📋 시스템 개요

News Analysis System은 **뉴스 검색, AI 분석, 캐시 관리**를 제공하는 마이크로서비스 아키텍처입니다.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Gateway       │    │  News Service   │
│   (React/Vue)   │◄──►│   (API Proxy)   │◄──►│   (Core API)    │
│   Port: 3000    │    │   Port: 8080    │    │   Port: 8002    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                │              ┌─────────────────┐
                                │              │     Redis       │
                                │              │   (Cache DB)    │
                                │              │   Port: 6379    │
                                │              └─────────────────┘
                                │                        │
                                │              ┌─────────────────┐
                                └──────────────│  Celery Worker  │
                                               │ (Background AI) │
                                               └─────────────────┘
```

## 🎯 각 서비스 역할

### 🌐 Gateway (`/gateway/`)
- **역할**: API 프록시 및 라우팅
- **포트**: 8080
- **용도**: 프론트엔드의 단일 진입점
- **특징**: 동적 프록시로 모든 요청을 News Service로 전달

### 📰 News Service (`/news-service/`)
- **역할**: 핵심 비즈니스 로직
- **포트**: 8002
- **기능**: 뉴스 검색, AI 분석, 캐시 관리, 대시보드
- **특징**: Redis 캐시 및 Celery 백그라운드 처리

### 🛠️ NewsTun Service (`/newstun-service/`)
- **역할**: ML 모델 학습 및 추론
- **용도**: AI 모델 개발 및 실험
- **상태**: 개발 중 (프로덕션 미사용)

## 🚀 빠른 시작 (프론트엔드 개발자용)

### 1️⃣ 전체 시스템 실행
```bash
# 모든 서비스 실행 (Gateway + News Service + Redis + Celery)
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

### 2️⃣ API 테스트
```bash
# 전체 엔드포인트 테스트
chmod +x test-endpoints.sh
./test-endpoints.sh
```

### 3️⃣ 프론트엔드 연결
```typescript
// 기본 설정
const GATEWAY_URL = 'http://localhost:8080';
const API_BASE = `${GATEWAY_URL}/gateway/v1/news`;

// 뉴스 검색 예시
const searchNews = async (query: string) => {
  const response = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, max_results: 10 })
  });
  return await response.json();
};
```

## 📂 디렉토리 구조

```
📦 News Analysis System
├── 🌐 gateway/                 # API Gateway (프론트엔드 진입점)
│   ├── app/
│   │   ├── domain/
│   │   │   ├── controller/     # 요청 처리 로직
│   │   │   ├── model/          # 데이터 모델
│   │   │   └── service/        # 비즈니스 로직
│   │   └── main.py            # Gateway 메인 애플리케이션
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md              # 🎯 프론트엔드 개발자 가이드
│
├── 📰 news-service/           # 핵심 뉴스 서비스
│   ├── app/
│   │   ├── api/
│   │   │   └── unified_router.py  # 통합 API 라우터
│   │   ├── domain/
│   │   │   ├── controller/     # API 컨트롤러
│   │   │   ├── model/          # 데이터 모델
│   │   │   └── service/        # 비즈니스 서비스
│   │   ├── core/              # 핵심 설정 및 의존성
│   │   ├── workers/           # Celery 작업자
│   │   └── main.py           # 서비스 메인 애플리케이션
│   ├── docker-compose.*.yml  # 다양한 실행 환경
│   └── README.md            # 서비스 상세 가이드
│
├── 🛠️ newstun-service/        # ML 모델 개발 환경
│   └── app/                  # (개발 중, 프로덕션 미사용)
│
├── 🐳 docker-compose.yml      # 전체 시스템 통합 실행
├── 🧪 test-endpoints.sh       # API 테스트 스크립트
└── 📖 README.md              # 📍 현재 파일 (전체 가이드)
```

## 🎯 프론트엔드 개발자 가이드

### 🔗 **주요 URL**
- **Gateway API**: `http://localhost:8080/gateway/v1/news/`
- **Swagger UI**: `http://localhost:8080/docs`
- **News Service 직접**: `http://localhost:8002/` (선택사항)

### 📝 **핵심 API 패턴**
```bash
# 뉴스 검색
POST /gateway/v1/news/search

# 회사 뉴스 검색  
POST /gateway/v1/news/companies/{company}

# 회사 뉴스 AI 분석
POST /gateway/v1/news/companies/{company}/analyze

# 대시보드 상태
GET /gateway/v1/news/dashboard/status

# 캐시 관리
GET /gateway/v1/news/cache/info  
DELETE /gateway/v1/news/cache/{company}
```

### 📚 **상세 문서**
- **[Gateway API 완전 가이드](./gateway/README.md)** ← 🎯 **프론트엔드 개발자 필수 문서**
- **[News Service 기술 문서](./news-service/README.md)**

## 🔧 개발 환경 설정

### 📦 Docker Compose (권장)
```bash
# 전체 시스템 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 재시작
docker-compose restart gateway
docker-compose restart news-service

# 시스템 종료
docker-compose down
```

### 🐛 개별 서비스 실행 (디버깅용)
```bash
# Gateway만 실행
cd gateway
python -m app.main

# News Service만 실행  
cd news-service
python -m app.main
```

## 📊 시스템 모니터링

### 🔍 **상태 확인**
```bash
# 전체 시스템 상태
curl http://localhost:8080/gateway/v1/health

# 서비스 연결 테스트
curl http://localhost:8080/gateway/v1/debug/connection

# 대시보드 상태
curl http://localhost:8080/gateway/v1/news/dashboard/status
```

### 📈 **성능 지표**
- **캐시 히트율**: 일반적으로 80% 이상
- **응답 시간**: 캐시 히트 시 < 100ms, 캐시 미스 시 < 2초
- **백그라운드 분석**: Celery로 비동기 처리

## 🌟 주요 특징

### ✅ **프론트엔드 친화적**
- **단일 진입점**: Gateway 하나로 모든 API 접근
- **일관된 구조**: 모든 엔드포인트가 동일한 패턴
- **자동 캐시**: 빠른 응답 속도 보장

### 🚀 **확장 가능한 아키텍처**
- **마이크로서비스**: 독립적인 서비스 확장
- **동적 프록시**: 새 API 자동 지원
- **Redis 캐시**: 고성능 데이터 캐싱

### 🛡️ **안정성**
- **에러 처리**: 상세한 에러 메시지
- **로깅**: 모든 요청/응답 로깅
- **헬스체크**: 실시간 상태 모니터링

## 🆘 문제 해결

### ❓ **자주 묻는 질문**

**Q: Gateway vs News Service 직접 호출?**
- **A**: **Gateway 사용 권장** (`http://localhost:8080/gateway/v1/news/`)
- 이유: 프록시 기능, 로깅, 에러 처리 통합

**Q: 캐시가 작동하지 않아요**
- **A**: Redis 상태 확인 `docker-compose logs redis`
- 캐시 정보 확인: `curl http://localhost:8080/gateway/v1/news/cache/info`

**Q: 분석이 느려요**
- **A**: 첫 요청은 실시간 분석 (느림), 두 번째부터는 캐시 (빠름)
- Celery 상태 확인: `docker-compose logs celery-worker`

### 🔧 **로그 확인**
```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f gateway
docker-compose logs -f news-service
docker-compose logs -f redis
docker-compose logs -f celery-worker
```

## 📞 지원 및 문의

- **API 문서**: http://localhost:8080/docs
- **시스템 상태**: `docker-compose ps`

## 🔮 로드맵

- [x] 뉴스 검색 API
- [x] AI 감정 분석
- [x] ESG 점수 분석  
- [x] Redis 캐시 시스템
- [x] 대시보드 API
- [x] 동적 프록시 Gateway
- [ ] 사용자 인증 시스템
- [ ] Rate Limiting
- [ ] 다국어 뉴스 지원
- [ ] 실시간 알림 시스템

---

## 🎯 **프론트엔드 개발자 시작점**

👉 **[Gateway API 완전 가이드](./gateway/README.md)**를 먼저 읽어보세요!

모든 API 사용법, 코드 예시, 그리고 실용적인 가이드가 포함되어 있습니다. 