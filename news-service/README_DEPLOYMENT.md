# News Service - 배포 가이드

## 📋 최신 업데이트 (v2.0)

### ✅ 해결된 문제들
1. **중복 프리픽스 문제** - API 엔드포인트 경로 정상화 완료
2. **헬스체크 로그 노이즈** - 불필요한 주기적 로그 제거
3. **외부 모델 마운트** - `newstun-service/models` 디렉토리 연동 개선
4. **키워드 폴백 이슈** - 모델 로딩 실패 시 상세 오류 메시지 제공
5. **보안 강화** - 환경변수를 안전하게 관리하는 방법 적용

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
파인튜닝된 모델을 사용한 뉴스 분석 서비스입니다. CPU와 GPU 두 가지 환경을 지원합니다.

## 파일 구조
```
news-service/
├── Dockerfile.cpu          # CPU 최적화 Dockerfile
├── Dockerfile.gpu          # GPU 최적화 Dockerfile  
├── docker-compose.cpu.yml  # CPU 환경 설정
├── docker-compose.gpu.yml  # GPU 환경 설정
├── switch_model.sh         # 모델 변경 스크립트 (Linux/Mac)
├── switch_model.bat        # 모델 변경 스크립트 (Windows)
└── app/                    # 애플리케이션 코드
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

#### ⚠️ 기존 방법 (보안상 비권장)
```bash
# 환경변수를 직접 노출하는 방법 (비권장)
docker run -d --name news-service-cpu -p 8002:8002 \
  -v "$(pwd)/../newstun-service/models:/app/models" \
  --env-file .env \
  -e MODEL_NAME=test222 \
  news-service:cpu-ultra-light
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
docker-compose -f docker-compose.gpu.yml down

# 새로운 모델로 시작
MODEL_NAME=test222 docker-compose -f docker-compose.cpu.yml up -d
```

## 성능 비교

### CPU vs GPU
| 환경 | 예상 처리 시간 | 메모리 사용량 | 배치 처리 |
|------|---------------|---------------|-----------|
| CPU  | 2-5초/뉴스    | 2-4GB        | 제한적    |
| GPU  | 0.1-0.5초/뉴스 | 4-8GB + GPU  | 우수      |

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

## 상태 확인

### 헬스체크
```bash
curl http://localhost:8002/health
# 응답: {"status": "healthy", "service": "news-service"}
```

### 로그 확인
```bash
# CPU 환경
docker-compose -f docker-compose.cpu.yml logs -f

# GPU 환경
docker-compose -f docker-compose.gpu.yml logs -f

# 디바이스 확인
docker-compose -f docker-compose.cpu.yml logs | grep "디바이스"
```

### 예상 로그
```
# CPU 환경 (정상 동작)
✅ 로컬 ML 추론 서비스 초기화 완료
ML 추론 서비스 초기화 - 디바이스: cpu
CUDA를 사용할 수 없습니다. CPU 모드로 실행됩니다.
카테고리 모델 로드 완료: test222_category
감정 모델 로드 완료: test222_sentiment

# GPU 환경  
✅ 로컬 ML 추론 서비스 초기화 완료
ML 추론 서비스 초기화 - 디바이스: cuda:0
CUDA 버전: 12.1
GPU 개수: 1
현재 GPU: NVIDIA GeForce RTX 4090

# 모델 로드 실패 시 (키워드 폴백)
카테고리 모델을 찾을 수 없습니다: /app/models/test222_category
감정 모델을 찾을 수 없습니다: /app/models/test222_sentiment
모든 모델 로드에 실패했습니다. 키워드 기반 분석으로 대체됩니다.
```

## 트러블슈팅

### 1. 중복 프리픽스 문제 (해결됨)
**증상**: API 경로가 `/api/v1/news/api/v1/news/...`로 중복 표시  
**해결**: `news_router.py`에서 중복 태그 제거됨
```bash
# 정상 엔드포인트 확인
curl http://localhost:8002/api/v1/news/company/simple/analyze
```

### 2. 헬스체크 로그 노이즈 (해결됨)
**증상**: 30초마다 헬스체크 로그 출력으로 중요 로그 가려짐  
**해결**: `Dockerfile.cpu`에서 HEALTHCHECK 비활성화됨
```bash
# 이제 깔끔한 로그만 출력됨
docker logs news-service-cpu
```

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
  -e MODEL_NAME=test222 \
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

## API 사용법

### 뉴스 분석 (실제 작동하는 엔드포인트)

#### PowerShell에서 API 테스트 (권장)
```powershell
# 간단한 분석
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/news/company/simple/analyze" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"company": "삼성전자"}' | 
  Select-Object -ExpandProperty Content

# 상세 분석
Invoke-WebRequest -Uri "http://localhost:8002/api/v1/news/company/simple" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"company": "삼성전자", "max_results": 10}' |
  Select-Object -ExpandProperty Content

# Python을 이용한 간단한 테스트 (PowerShell에서)
python -c "import requests; r = requests.post('http://localhost:8002/api/v1/news/company/simple/analyze', json={'company': '삼성전자'}); print(f'상태: {r.status_code}'); print(r.json()['ml_service_status'] if r.status_code == 200 else 'Error')"
```

#### Linux/Mac/WSL에서 API 테스트
```bash
# 간단한 분석
curl -X POST http://localhost:8002/api/v1/news/company/simple/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "company": "삼성전자"
  }'

# 상세 분석
curl -X POST http://localhost:8002/api/v1/news/company/simple \
  -H "Content-Type: application/json" \
  -d '{
    "company": "삼성전자",
    "max_results": 10
  }'
```

### 응답 예시
```json
{
  "company": "삼성전자",
  "ml_service_status": "local_model",
  "analyzed_news": [
    {
      "title": "삼성전자, ESG 경영 강화 발표",
      "url": "https://news.example.com/...",
      "summary": "삼성전자가 환경 친화적 경영 방침을 발표했다...",
      "esg_classification": {
        "category": "E",
        "confidence": 0.95,
        "reasoning": "환경 관련 내용 포함"
      },
      "sentiment_analysis": {
        "label": "긍정",
        "confidence": 0.87,
        "reasoning": "긍정적 표현 다수 포함"
      },
      "published_date": "2024-01-15",
      "news_source": "조선비즈"
    }
  ],
  "summary": {
    "total_analyzed": 41,
    "esg_distribution": {
      "E": 15,
      "S": 12,
      "G": 8,
      "기타": 6
    },
    "sentiment_distribution": {
      "긍정": 28,
      "중립": 10,
      "부정": 3
    }
  }
}
```

## 운영 권장사항

### 1. 보안 운영 가이드

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

### 2. 리소스 모니터링

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

### 3. 로그 로테이션
```yaml
# docker-compose.yml에 추가
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 4. 자동 재시작
```yaml
restart: unless-stopped  # 이미 설정됨
```

## 환경별 선택 가이드

### CPU 환경 권장
- 개발/테스트 환경
- 소규모 처리량 (<100 뉴스/일)
- GPU 없는 서버

### GPU 환경 권장  
- 프로덕션 환경
- 대용량 처리 (>1000 뉴스/일)
- 실시간 분석 요구사항 

# News Service 배포 가이드 (용량 최적화)

## 🚀 배포 옵션

### 1. CPU 버전 (권장 - 경량)
```bash
docker-compose -f docker-compose.cpu.yml up -d
```
- **예상 용량**: ~2-3GB
- **메모리 사용량**: ~1-2GB
- **성능**: 중간 (CPU 추론)

### 2. GPU 버전 (최적화됨)
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

## 📊 성능 비교

| 버전 | 이미지 크기 | 메모리 사용량 | 빌드 시간 | 추론 속도 |
|------|-------------|---------------|-----------|-----------|
| CPU | ~2-3GB | ~1-2GB | ~5분 | 보통 |
| GPU (최적화 전) | ~26GB | ~8GB | ~20분 | 빠름 |
| GPU (최적화 후) | ~6-8GB | ~2-4GB | ~10분 | 빠름 |

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
2. **메모리**: 최소 4GB RAM 권장
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