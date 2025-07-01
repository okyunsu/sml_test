# News Service v2.0 - 배포 가이드

## 📋 최신 업데이트 (v2.0 - 통합 라우터 시스템)

### ✅ v2.0 주요 개선사항
1. **통합 라우터 시스템** - 사용 목적별로 분리된 API 구조
2. **스마트 캐시 전략** - Redis 기반 지능형 캐싱 시스템
3. **Clean Architecture 적용** - 의존성 주입 및 계층 분리
4. **성능 최적화** - 43% 코드 감소, 응답 시간 개선
5. **보안 강화** - 환경변수를 안전하게 관리하는 방법 적용

### 🎯 새로운 API 구조
```
/api/v1/search/                    # 🔍 스마트 검색 (캐시 우선 → 실시간)
├── news                          # 일반 뉴스 검색
├── companies/{company}           # 회사 뉴스 검색
├── companies/{company}/analyze   # 회사 뉴스 분석
├── batch                         # 배치 검색
└── trending                      # 트렌딩 키워드

/api/v1/dashboard/                # 📊 대시보드 (백그라운드 데이터)
├── status                        # 전체 상태
├── companies/{company}/latest    # 회사 최신 분석
├── companies/{company}/history   # 분석 히스토리
├── companies/{company}/trigger   # 백그라운드 분석 요청
└── cache/                        # 캐시 관리

/api/v1/system/                   # 🛠️ 시스템 관리
├── health                        # 헬스체크
└── test/                         # 시스템 테스트
```

### 🚀 권장 실행 방법

#### Windows PowerShell (권장 - 보안 강화)
```powershell
# 1. 이미지 빌드
docker build -f Dockerfile.cpu -t news-service:cpu-ultra-light .

# 2. 보안 강화된 방법 - .env 파일 마운트 (권장)
docker run -d --name news-service-cpu -p 8002:8002 `
  -v "${PWD}/../newstun-service/models:/app/models" `
  -v "${PWD}/.env:/app/.env:ro" `
  news-service:cpu-ultra-light

# 3. 상태 확인
docker ps
docker logs news-service-cpu --tail 10

# 4. 환경변수 확인 (선택사항)
docker exec news-service-cpu env | Select-String "MODEL\|NAVER"
```

#### Linux/Mac/WSL (보안 강화)
```bash
# 1. 이미지 빌드
docker build -f Dockerfile.cpu -t news-service:cpu-ultra-light .

# 2. 보안 강화된 방법 - .env 파일 마운트 (권장)
docker run -d --name news-service-cpu -p 8002:8002 \
  -v "$(pwd)/../newstun-service/models:/app/models" \
  -v "$(pwd)/.env:/app/.env:ro" \
  news-service:cpu-ultra-light

# 3. 상태 확인
docker ps
docker logs news-service-cpu --tail 10
```

#### ⚠️ 비권장 방법 (보안 위험)
```bash
# 환경변수를 명령어에 직접 노출 (보안상 위험)
docker run -d --name news-service-cpu -p 8002:8002 \
  -v "$(pwd)/../newstun-service/models:/app/models" \
  -e MODEL_NAME=test222 \
  -e NAVER_CLIENT_ID=your_id \
  -e NAVER_CLIENT_SECRET=your_secret \
  news-service:cpu-ultra-light
```

## 개요
파인튜닝된 모델을 사용한 뉴스 분석 서비스입니다. CPU와 GPU 두 가지 환경을 지원하며, v2.0에서는 통합 라우터 시스템과 스마트 캐시 기능이 추가되었습니다.

## 파일 구조
```
news-service/
├── Dockerfile.cpu                 # CPU 최적화 Dockerfile
├── Dockerfile.gpu                 # GPU 최적화 Dockerfile  
├── docker-compose.cpu.yml         # CPU 환경 설정
├── docker-compose.redis.yml       # Redis + 대시보드 환경 (권장)
├── docker-compose.gpu.yml         # GPU 환경 설정
├── DOCKER_COMMANDS.txt            # Docker 명령어 모음
└── app/                           # 애플리케이션 코드
    ├── api/
    │   └── unified_router.py      # 통합 라우터 시스템
    ├── core/
    │   ├── dependencies.py        # 의존성 주입 컨테이너
    │   ├── exceptions.py          # 공통 예외 처리
    │   └── http_client.py         # HTTP 클라이언트 관리
    └── domain/
        ├── controller/            # 컨트롤러 계층
        ├── service/               # 서비스 계층
        └── model/                 # 모델 계층
```

## 사전 요구사항

### 공통
- Docker & Docker Compose
- newstun-service/models 디렉토리에 파인튜닝된 모델
- `.env` 파일 설정 (보안 필수)

### GPU 환경 (추가)
- NVIDIA GPU 드라이버
- NVIDIA Container Toolkit

## 🔒 보안 설정

### .env 파일 생성 (필수)
```bash
# .env 파일 생성
cat > .env << EOF
# Naver API 설정
NAVER_CLIENT_ID=your_actual_client_id
NAVER_CLIENT_SECRET=your_actual_client_secret

# 모델 설정
MODEL_NAME=test222

# 서비스 설정 (선택사항)
LOG_LEVEL=INFO

# Redis 설정 (대시보드 기능 사용 시)
REDIS_URL=redis://localhost:6379/0
EOF
```

### 파일 권한 설정 (권장)
```bash
# Linux/Mac - .env 파일 권한을 소유자만 읽기 가능하도록 설정
chmod 600 .env

# Windows PowerShell - 파일 권한 제한
icacls .env /inheritance:d /grant:r "${env:USERNAME}:R"
```

### 보안 체크리스트
- ✅ `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- ✅ 실제 API 키가 버전 관리에 포함되지 않는지 확인  
- ✅ `.env` 파일을 읽기 전용(`:ro`)으로 마운트
- ✅ 환경변수를 Docker 명령어에 직접 노출하지 않기
- ✅ 프로덕션과 개발 환경의 `.env` 파일 분리

## 빌드 및 실행

### 1. CPU 환경 (권장 - 보안 강화)

#### 🔒 보안 강화된 방법 (권장)
```bash
# 이미지 빌드
docker build -f Dockerfile.cpu -t news-service:cpu-ultra-light .

# .env 파일을 안전하게 마운트하여 실행
docker run -d --name news-service-cpu -p 8002:8002 \
  -v "$(pwd)/../newstun-service/models:/app/models" \
  -v "$(pwd)/.env:/app/.env:ro" \
  news-service:cpu-ultra-light

# Docker Compose 사용 시 (자동으로 .env 파일 로드)
docker-compose -f docker-compose.cpu.yml up -d
```

#### 🚀 Redis 포함 실행 (대시보드 기능 - 권장)
```bash
# Redis + Celery + 대시보드 기능 포함
docker-compose -f docker-compose.redis.yml up -d

# 로그 확인 (모든 서비스)
docker-compose -f docker-compose.redis.yml logs -f

# 특정 서비스 로그만 확인
docker-compose -f docker-compose.redis.yml logs -f news-service
```

#### 설정 요구사항
- **필수**: `../newstun-service/models` 디렉토리에 파인튜닝된 모델 존재 확인
- **필수**: `.env` 파일에 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `MODEL_NAME` 설정
- **권장**: 외부 모델 디렉토리를 `/app/models`로 마운트하여 사용
- **보안**: `.env` 파일을 읽기 전용(`:ro`)으로 마운트

### 2. GPU 환경
```bash
# 이미지 빌드
docker build -f Dockerfile.gpu -t news-service:gpu .

# 실행 (기본: test123 모델)
docker-compose -f docker-compose.gpu.yml up -d

# 다른 모델 사용
MODEL_NAME=test222 docker-compose -f docker-compose.gpu.yml up -d
```

## 모델 변경

### 스크립트 사용 (권장)
```bash
# Linux/Mac
./switch_model.sh cpu test222    # CPU 환경에서 test222 모델
./switch_model.sh gpu test123    # GPU 환경에서 test123 모델

# Windows
switch_model.bat cpu test222     # CPU 환경에서 test222 모델
switch_model.bat gpu test123     # GPU 환경에서 test123 모델
```

### 수동 변경
```bash
# 기존 컨테이너 중지
docker-compose -f docker-compose.cpu.yml down
docker-compose -f docker-compose.redis.yml down
docker-compose -f docker-compose.gpu.yml down

# 새로운 모델로 시작
MODEL_NAME=test222 docker-compose -f docker-compose.cpu.yml up -d
```

## 성능 비교

### CPU vs GPU vs Redis 환경
| 환경 | 예상 처리 시간 | 메모리 사용량 | 배치 처리 | 캐시 기능 |
|------|---------------|---------------|-----------|-----------|
| CPU  | 2-5초/뉴스    | 2-4GB        | 제한적    | ❌        |
| CPU+Redis | 100ms/뉴스 (캐시 히트) | 3-5GB | 우수 | ✅ |
| GPU  | 0.1-0.5초/뉴스 | 4-8GB + GPU  | 최고     | ❌        |

### 이미지 크기
- **CPU**: ~2-3GB (CPU 전용 PyTorch)
- **GPU**: ~4-5GB (CUDA 포함)

## 모델 지원

### 현재 지원 모델
- **test123**: 기본 파인튜닝 모델
- **test222**: 대안 파인튜닝 모델

### 모델 구조
각 모델은 다음 두 부분으로 구성:
- `{모델명}_category`: ESG 카테고리 분류
- `{모델명}_sentiment`: 감정 분석

## 🧪 v2.0 API 테스트

### 헬스체크
```bash
curl http://localhost:8002/api/v1/system/health
# 응답: {"status": "healthy", "service": "news-service", "version": "2.0"}
```

### 🔍 스마트 검색 API 테스트

#### 1. 회사 뉴스 검색 (스마트 캐시)
```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/search/companies/삼성전자" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"max_results": 10}' |
  Select-Object -ExpandProperty Content

# Linux/Mac/WSL
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자 \
  -H "Content-Type: application/json" \
  -d '{"max_results": 10}'
```

#### 2. 회사 뉴스 분석 (스마트 캐시)
```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/search/companies/삼성전자/analyze" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"max_results": 50, "force_refresh": false}' |
  Select-Object -ExpandProperty Content

# Linux/Mac/WSL
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자/analyze \
  -H "Content-Type: application/json" \
  -d '{"max_results": 50, "force_refresh": false}'
```

#### 3. 일반 뉴스 검색
```bash
curl -X POST http://localhost:8002/api/v1/search/news \
  -H "Content-Type: application/json" \
  -d '{"query": "ESG", "max_results": 10}'
```

### 📊 대시보드 API 테스트 (Redis 환경 필요)

#### 1. 전체 상태 조회
```bash
curl http://localhost:8002/api/v1/dashboard/status
```

#### 2. 회사 최신 분석 결과
```bash
curl http://localhost:8002/api/v1/dashboard/companies/삼성전자/latest
```

#### 3. 백그라운드 분석 요청
```bash
curl -X POST http://localhost:8002/api/v1/dashboard/companies/삼성전자/trigger
```

### 🛠️ 시스템 관리 API 테스트

#### 1. 통합 테스트
```bash
curl http://localhost:8002/api/v1/system/test/integration
```

## 상태 확인

### 로그 확인
```bash
# CPU 환경
docker-compose -f docker-compose.cpu.yml logs -f

# Redis 환경 (권장)
docker-compose -f docker-compose.redis.yml logs -f

# GPU 환경
docker-compose -f docker-compose.gpu.yml logs -f

# 디바이스 확인
docker-compose -f docker-compose.cpu.yml logs | grep "디바이스"
```

### 예상 로그 (v2.0)
```
# 정상 시작 로그
✅ News Service v2.0 시작 완료
🔧 통합 라우터 시스템 로드 완료
🔗 의존성 주입 컨테이너 초기화 완료
⚡ 스마트 캐시 시스템 준비 완료 (Redis 연결 시)

# ML 서비스 초기화
✅ 로컬 ML 추론 서비스 초기화 완료
ML 추론 서비스 초기화 - 디바이스: cpu
CUDA를 사용할 수 없습니다. CPU 모드로 실행됩니다.
카테고리 모델 로드 완료: test222_category
감정 모델 로드 완료: test222_sentiment

# API 요청 처리 로그
🔍 스마트 검색 요청: company=삼성전자, cache_hit=true, response_time=120ms
📊 대시보드 상태 조회: redis_connected=true
```

## v2.0 응답 예시

### 스마트 검색 응답
```json
{
  "search_metadata": {
    "company": "삼성전자",
    "total_found": 1247,
    "returned_count": 50,
    "cache_hit": true,
    "response_time_ms": 120,
    "search_time": "2024-01-15T10:30:00Z"
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

### 분석 응답
```json
{
  "analysis_metadata": {
    "company": "삼성전자",
    "analyzed_count": 50,
    "analysis_time": "2024-01-15T10:30:00Z",
    "ml_service_status": "local_model",
    "cache_hit": false,
    "processing_time_ms": 3450
  },
  "analyzed_news": [
    {
      "title": "삼성전자, ESG 경영 강화 발표",
      "url": "https://example.com/news/123",
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
      }
    }
  ],
  "summary": {
    "total_analyzed": 50,
    "esg_distribution": {"E": 20, "S": 15, "G": 10, "기타": 5},
    "sentiment_distribution": {"긍정": 35, "중립": 12, "부정": 3},
    "top_keywords": ["환경", "ESG", "지속가능경영"]
  }
}
```

## 트러블슈팅

### 1. v2.0 관련 문제

#### 통합 라우터 404 오류
**증상**: 기존 API 엔드포인트 호출 시 404 오류  
**해결**: 새로운 API 구조 사용
```bash
# ❌ 구 버전 (더 이상 사용 불가)
curl http://localhost:8002/api/v1/news/company/simple/analyze

# ✅ v2.0 새 버전
curl -X POST http://localhost:8002/api/v1/search/companies/삼성전자/analyze
```

#### 캐시 기능 작동 안함
**증상**: 항상 `cache_hit: false`로 응답  
**해결**: Redis 포함 환경으로 실행
```bash
# Redis 포함 실행
docker-compose -f docker-compose.redis.yml up -d

# Redis 연결 확인
docker-compose -f docker-compose.redis.yml logs redis
```

### 2. 기존 문제들 (해결됨)

#### 중복 프리픽스 문제 (해결됨)
**상태**: v2.0에서 통합 라우터로 완전 해결  

#### 헬스체크 로그 노이즈 (해결됨)
**상태**: v2.0에서 시스템 API로 분리하여 해결

### 3. 모델 로드 실패

#### PowerShell에서 확인
```powershell
# 모델 경로 및 파일 확인
ls ../newstun-service/models/
ls ../newstun-service/models/test222*

# 컨테이너 내부 모델 마운트 확인
docker exec news-service-cpu ls -la /app/models/

# 현재 디렉토리 확인
Get-Location
"${PWD}/../newstun-service/models"
```

#### Linux/Mac/WSL에서 확인
```bash
# 모델 경로 및 파일 확인
ls -la ../newstun-service/models/
ls -la ../newstun-service/models/test222*

# 권한 확인
chmod -R 755 ../newstun-service/models/

# 컨테이너 내부 모델 마운트 확인
docker exec news-service-cpu ls -la /app/models/
```

### 4. 키워드 폴백 모드 문제
**증상**: "모든 모델 로드에 실패했습니다. 키워드 기반 분석으로 대체됩니다."  
**해결 방법**:
```bash
# 1. 모델 파일 존재 확인
ls ../newstun-service/models/test222_category/
ls ../newstun-service/models/test222_sentiment/

# 2. 올바른 MODEL_NAME 환경변수 설정
docker run -d --name news-service-cpu -p 8002:8002 \
  -v "$(pwd)/../newstun-service/models:/app/models" \
  -v "$(pwd)/.env:/app/.env:ro" \
  news-service:cpu-ultra-light

# 3. 로그에서 모델 로딩 상태 확인
docker logs news-service-cpu | grep -E "(모델|ML|추론)"
```

### 5. GPU 인식 안됨
```bash
# GPU 상태 확인
nvidia-smi

# Docker GPU 지원 확인
docker run --rm --gpus all nvidia/cuda:12.1-base nvidia-smi
```

### 6. 메모리 부족
```yaml
# docker-compose.yml에서 메모리 제한 조정
deploy:
  resources:
    limits:
      memory: 8G  # 필요에 따라 증가
```

### 7. 포트 충돌
```yaml
# 다른 포트 사용
ports:
  - "8003:8002"  # 호스트 포트 변경
```

### 8. PowerShell 관련 문제
**증상**: PowerShell에서 백슬래시(`\`) 줄바꿈이나 `$(pwd)` 명령어 오류  
**해결 방법**:
```powershell
# ❌ 잘못된 방법 (Bash 문법 + 보안 위험)
docker run -d --name news-service-cpu -p 8002:8002 \
  -v "$(pwd)/../newstun-service/models:/app/models" \
  -e MODEL_NAME=test222 \
  -e NAVER_CLIENT_ID=your_id news-service:cpu-ultra-light

# ✅ 올바른 방법 (PowerShell 문법 + 보안 강화)
docker run -d --name news-service-cpu -p 8002:8002 `
  -v "${PWD}/../newstun-service/models:/app/models" `
  -v "${PWD}/.env:/app/.env:ro" `
  news-service:cpu-ultra-light

# 한 줄로 작성 시
docker run -d --name news-service-cpu -p 8002:8002 -v "${PWD}/../newstun-service/models:/app/models" -v "${PWD}/.env:/app/.env:ro" news-service:cpu-ultra-light
```

### 9. 환경변수 보안 문제
**증상**: API 키가 Docker 명령어 히스토리에 노출되거나 프로세스 목록에서 보임  
**해결 방법**:
```powershell
# ❌ 보안 위험 - 명령어에 직접 노출
docker run -e NAVER_CLIENT_SECRET=your_secret ...

# ✅ 보안 강화 - .env 파일 사용
docker run -v "${PWD}/.env:/app/.env:ro" ...

# 환경변수 확인 (안전한 방법)
docker exec news-service-cpu env | Select-String "MODEL_NAME"
docker exec news-service-cpu env | Select-String "NAVER_CLIENT_ID"
# NAVER_CLIENT_SECRET은 보안상 확인하지 않음
```

## 운영 권장사항

### 1. v2.0 환경별 선택 가이드

#### 개발 환경
```bash
# 기본 개발 (캐시 없음)
docker-compose -f docker-compose.cpu.yml up -d

# 고급 개발 (캐시 포함)
docker-compose -f docker-compose.redis.yml up -d
```

#### 프로덕션 환경
```bash
# 중간 규모 (권장)
docker-compose -f docker-compose.redis.yml up -d

# 대용량 처리
docker-compose -f docker-compose.gpu.yml up -d
```

### 2. 보안 운영 가이드

#### .env 파일 관리
```bash
# 개발환경과 프로덕션 환경 분리
cp .env.example .env.dev
cp .env.example .env.prod

# 프로덕션 배포 시
docker run -v "$(pwd)/.env.prod:/app/.env:ro" ...

# 정기적인 API 키 로테이션
# 1. Naver API 콘솔에서 새 키 생성
# 2. .env 파일 업데이트
# 3. 컨테이너 재시작
```

#### 보안 모니터링
```powershell
# API 키 노출 여부 확인
docker history news-service:cpu-ultra-light | Select-String "NAVER"
git log --oneline -p | Select-String "NAVER_CLIENT"

# 컨테이너 권한 확인
docker inspect news-service-cpu | Select-String "Privileged\|User"
```

### 3. 성능 모니터링

#### v2.0 성능 메트릭
```bash
# 캐시 적중률 확인 (Redis 환경)
curl http://localhost:8002/api/v1/dashboard/cache/info

# API 응답 시간 확인
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8002/api/v1/system/health

# 시스템 리소스 모니터링
docker stats news-service-cpu
```

#### curl-format.txt 파일 생성
```bash
cat > curl-format.txt << EOF
     time_namelookup:  %{time_namelookup}s\n
        time_connect:  %{time_connect}s\n
     time_appconnect:  %{time_appconnect}s\n
    time_pretransfer:  %{time_pretransfer}s\n
       time_redirect:  %{time_redirect}s\n
  time_starttransfer:  %{time_starttransfer}s\n
                     ----------\n
          time_total:  %{time_total}s\n
EOF
```

### 4. 리소스 모니터링

#### PowerShell
```powershell
# 컨테이너 리소스 사용량
docker stats

# GPU 사용량 (GPU 환경) - PowerShell에서 반복 실행
while ($true) { Clear-Host; nvidia-smi; Start-Sleep 1 }

# 로그 실시간 모니터링 (민감정보 필터링)
docker logs news-service-cpu -f | Select-String -NotMatch "CLIENT_SECRET"
```

#### Linux/Mac/WSL
```bash
# 컨테이너 리소스 사용량
docker stats

# GPU 사용량 (GPU 환경)
watch -n 1 nvidia-smi

# 보안 로그 모니터링
docker logs news-service-cpu -f | grep -v "CLIENT_SECRET"
```

### 5. 로그 로테이션
```yaml
# docker-compose.yml에 추가
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 6. 자동 재시작
```yaml
restart: unless-stopped  # 이미 설정됨
```

## 환경별 선택 가이드 (v2.0)

### CPU 환경 권장
- 개발/테스트 환경
- 소규모 처리량 (<100 뉴스/일)
- GPU 없는 서버
- 캐시 없는 단순 테스트

### CPU + Redis 환경 권장 (⭐ 추천)
- 일반적인 프로덕션 환경
- 중간 규모 처리량 (100-1000 뉴스/일)
- 대시보드 기능 필요
- 스마트 캐시 활용

### GPU 환경 권장  
- 고성능 프로덕션 환경
- 대용량 처리 (>1000 뉴스/일)
- 실시간 분석 요구사항 
- 최고 성능 필요

# News Service 배포 가이드 (용량 최적화)

## 🚀 배포 옵션

### 1. CPU 버전 (권장 - 경량)
```bash
docker-compose -f docker-compose.cpu.yml up -d
```
- **예상 용량**: ~2-3GB
- **메모리 사용량**: ~1-2GB
- **성능**: 중간 (CPU 추론)

### 2. CPU + Redis 버전 (⭐ 권장 - 스마트 캐시)
```bash
docker-compose -f docker-compose.redis.yml up -d
```
- **예상 용량**: ~3-4GB
- **메모리 사용량**: ~2-3GB
- **성능**: 빠름 (캐시 적중 시), 대시보드 기능

### 3. GPU 버전 (최적화됨)
```bash
docker-compose -f docker-compose.gpu.yml up -d
```
- **예상 용량**: ~6-8GB (기존 26GB → 대폭 감소)
- **메모리 사용량**: ~2-4GB
- **성능**: 빠름 (GPU 추론)

## 🎯 용량 최적화 적용 사항

### Docker 이미지 최적화
1. **베이스 이미지 변경**:
   - `nvidia/cuda:11.8.0-devel` → `nvidia/cuda:11.8.0-runtime`
   - 개발 도구 제거로 **~4GB 절약**

2. **PyTorch 버전 고정**:
   - 최신 버전 대신 안정된 버전 사용
   - `torch==2.0.1+cu118` 고정으로 **~2GB 절약**

3. **캐시 비활성화**:
   - pip, transformers, torch 캐시 비활성화
   - 임시 디렉토리를 tmpfs로 마운트

4. **멀티스테이지 빌드**:
   - 빌드 도구와 런타임 분리
   - 불필요한 파일 정리

### 메모리 최적화
1. **모델 로딩 최적화**:
   - `torch.float16` 사용 (GPU)
   - `local_files_only=True`
   - `low_cpu_mem_usage=True`

2. **GPU 메모리 관리**:
   - `torch.cuda.empty_cache()` 자동 호출
   - CUDNN 최적화 설정

## 📊 성능 비교 (v2.0)

| 버전 | 이미지 크기 | 메모리 사용량 | 빌드 시간 | 추론 속도 | 캐시 기능 |
|------|-------------|---------------|-----------|-----------|-----------|
| CPU | ~2-3GB | ~1-2GB | ~5분 | 보통 | ❌ |
| CPU+Redis | ~3-4GB | ~2-3GB | ~6분 | 빠름(캐시) | ✅ |
| GPU (최적화 전) | ~26GB | ~8GB | ~20분 | 빠름 | ❌ |
| GPU (최적화 후) | ~6-8GB | ~2-4GB | ~10분 | 빠름 | ❌ |

## 🛠️ 추가 최적화 옵션

### 1. 모델 양자화 (선택사항)
```bash
python optimize_models.py
```
- 모델 크기 **50-70% 감소**
- 성능 손실 **<5%**

### 2. 캐시 정리
```bash
# Docker 캐시 정리
docker system prune -a

# 이미지 정리
docker image prune -a
```

### 3. 환경변수 설정
```env
# .env 파일에 추가
HF_HOME=/tmp/huggingface
TRANSFORMERS_CACHE=/tmp/transformers_cache
TORCH_HOME=/tmp/torch_cache
PIP_NO_CACHE_DIR=1
```

## ⚠️ 주의사항

1. **GPU 드라이버**: CUDA 11.8 호환 드라이버 필요
2. **메모리**: 최소 4GB RAM 권장 (Redis 포함 시 6GB)
3. **디스크**: 최소 10GB 여유 공간 필요
4. **모델 파일**: `../newstun-service/models` 디렉토리 필요

## 🔧 문제 해결

### 용량 부족 시
1. CPU 버전 사용 고려
2. 모델 양자화 적용
3. Docker 캐시 정리

### 메모리 부족 시
1. `docker-compose.gpu.yml`에서 메모리 제한 조정
2. 다른 컨테이너 종료
3. GPU 메모리 확인

### 빌드 실패 시
1. Docker 재시작
2. 캐시 정리 후 재빌드
3. 인터넷 연결 확인 