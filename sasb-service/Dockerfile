# Stage 1: Build stage
FROM python:3.11-slim as builder

# Build 환경 최적화
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build dependencies 설치 (최소한으로)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage (최소 이미지)
FROM python:3.11-slim

# 런타임 환경 최적화
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/home/appuser/app

WORKDIR /app

# 런타임에 필요한 최소한의 패키지만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 비root 사용자 생성
RUN useradd --create-home --shell /bin/bash appuser

# Build stage에서 설치된 Python 패키지들만 복사 (전역 설치로 변경)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 및 공통 모듈 복사 (ROOT 권한으로)
COPY ./app /home/appuser/app/app
COPY ./shared /home/appuser/app/shared
COPY start.sh /home/appuser/app/

# 모델 디렉토리 생성 및 권한 설정 (ROOT 권한으로)
RUN mkdir -p /home/appuser/app/shared/models
RUN chown -R appuser:appuser /home/appuser/app
RUN chmod +x /home/appuser/app/start.sh

# 디렉토리 구조 검증
RUN ls -la /home/appuser/app/shared || echo "❗ Warning: shared directory not found"

# 이제 appuser로 전환
USER appuser
WORKDIR /home/appuser/app

# Railway는 동적 포트 할당하므로 EXPOSE 불필요

# 헬스체크 (더 효율적으로)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8003/health || exit 1

# start.sh 실행 (절대 경로)  
CMD ["/bin/bash", "/home/appuser/app/start.sh"] 