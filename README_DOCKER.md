# 🐳 Docker Compose 실행 가이드

News Service + Gateway + Redis + Celery를 Docker Compose로 한 번에 실행하는 가이드입니다.

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# news-service 환경변수 설정
cp news-service/.env.example news-service/.env
# news-service/.env 파일을 열어서 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET을 설정하세요
```

### 2. 모델 디렉토리 확인
```bash
# newstun-service 모델 디렉토리가 있는지 확인
ls -la newstun-service/models/
# 없다면 생성
mkdir -p newstun-service/models
```

### 3. 서비스 실행
```bash
# 전체 서비스 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build
```

## 📋 서비스 구성

### 포트 매핑
- **Gateway**: `http://localhost:8080` (외부 접근점)
- **News Service**: `http://localhost:8002` (내부 API)
- **Redis**: `localhost:6379` (캐시 및 큐)

### 서비스 아키텍처
```
외부 요청 ──▶ Gateway (8080) ──▶ News Service (8002)
                                        │
                                        ▼
               Redis (6379) ◀── Celery Worker (백그라운드 분석)
                     ▲              ▲
                     │              │
                Celery Beat ────────┘
               (30분마다 스케줄)
```

### 서비스 설명
1. **Gateway**: API 게이트웨이, 외부 요청 라우팅
2. **News Service**: 메인 뉴스 검색 및 분석 API
3. **Redis**: 캐시 저장소 및 Celery 메시지 브로커
4. **Celery Worker**: 백그라운드 뉴스 분석 작업 처리
5. **Celery Beat**: 정기적인 작업 스케줄링 (30분마다 회사 분석)

## 🛠️ 주요 명령어

### 서비스 관리
```bash
# 전체 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d gateway news-service redis

# 서비스 중지
docker-compose down

# 볼륨까지 삭제 (Redis 데이터 포함)
docker-compose down -v

# 서비스 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart gateway
```

### 로그 확인
```bash
# 전체 로그 확인
docker-compose logs

# 특정 서비스 로그
docker-compose logs gateway
docker-compose logs news-service
docker-compose logs celery-worker
docker-compose logs celery-beat

# 실시간 로그 확인
docker-compose logs -f
```

### 상태 확인
```bash
# 서비스 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker-compose top
```

## 🧪 API 테스트

### 헬스체크
```bash
# Gateway 헬스체크
curl http://localhost:8080/gateway/v1/health

# News Service 헬스체크 (직접)
curl http://localhost:8002/health
```

### 뉴스 검색 테스트
```bash
# Gateway를 통한 뉴스 검색
curl -X POST "http://localhost:8080/gateway/v1/news/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "삼성전자",
    "max_results": 5
  }'

# Gateway를 통한 회사 뉴스 검색
curl -X POST "http://localhost:8080/gateway/v1/news/companies/삼성전자"

# Gateway를 통한 회사 뉴스 분석
curl -X POST "http://localhost:8080/gateway/v1/news/companies/삼성전자/analyze"

# 대시보드 상태 확인
curl http://localhost:8080/gateway/v1/news/dashboard/status

# 시스템 헬스체크
curl http://localhost:8080/gateway/v1/news/system/health
```

### 캐시 및 백그라운드 작업 확인
```bash
# Redis 연결 테스트
docker-compose exec redis redis-cli ping

# Celery 작업 상태 확인
curl http://localhost:8080/gateway/v1/news/system/test/celery
```

## 🔧 환경 설정

### 필수 환경변수 (news-service/.env)
```env
# Naver API 키 (필수!)
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# 모델 설정
MODEL_NAME=test123
```

### 선택적 환경변수
```env
# CPU 최적화
OMP_NUM_THREADS=2
TOKENIZERS_PARALLELISM=false

# 로그 레벨
LOG_LEVEL=INFO
```

## 🔍 문제 해결

### 1. 포트 충돌
```bash
# 포트 사용 확인
netstat -tulpn | grep :8080
netstat -tulpn | grep :8002
netstat -tulpn | grep :6379

# 포트 변경이 필요한 경우 docker-compose.yml 수정
```

### 2. 모델 디렉토리 오류
```bash
# 모델 디렉토리 생성
mkdir -p newstun-service/models

# 권한 확인
ls -la newstun-service/models/
```

### 3. Redis 연결 오류
```bash
# Redis 컨테이너 상태 확인
docker-compose ps redis

# Redis 로그 확인
docker-compose logs redis

# Redis 연결 테스트
docker-compose exec redis redis-cli ping
```

### 4. Celery 작업 오류
```bash
# Celery Worker 로그 확인
docker-compose logs celery-worker

# Celery Beat 로그 확인
docker-compose logs celery-beat

# Celery 작업 재시작
docker-compose restart celery-worker celery-beat
```

### 5. 메모리 부족
```bash
# 리소스 사용량 확인
docker stats

# 메모리 제한 조정 (docker-compose.yml에서)
deploy:
  resources:
    limits:
      memory: 2G  # 필요에 따라 조정
```

## 📊 모니터링

### 리소스 사용량
```bash
# 실시간 리소스 모니터링
docker stats

# 특정 컨테이너 모니터링
docker stats news-service-api news-gateway
```

### 로그 모니터링
```bash
# 실시간 로그 (모든 서비스)
docker-compose logs -f

# 에러 로그만 필터링
docker-compose logs | grep -i error
```

## 🚀 성능 최적화

### 메모리 최적화
- News Service: 3GB 제한
- Celery Worker: 2.5GB 제한
- Gateway: 512MB 제한
- Redis: 기본 설정

### CPU 최적화
- News Service: 2 CPU 제한
- Celery Worker: 1.5 CPU 제한
- Gateway: 0.5 CPU 제한

이제 `docker-compose up -d --build` 명령어로 전체 시스템을 실행할 수 있습니다! 🎉 