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
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage (최소 이미지)
FROM python:3.11-slim

# 런타임 환경 최적화
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/home/appuser/app \
    PATH=/home/appuser/.local/bin:$PATH

WORKDIR /app

# 런타임에 필요한 최소한의 패키지만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 비root 사용자 생성
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser/app

# Build stage에서 설치된 Python 패키지들만 복사
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# 애플리케이션 코드 및 공통 모듈 복사
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./shared ./shared

# 시작 스크립트 복사
COPY --chown=appuser:appuser start.sh ./
RUN chmod +x start.sh

# Railway는 동적 포트 할당하므로 EXPOSE 불필요

# 헬스체크 (더 효율적으로)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8003/health || exit 1

# 최소 테스트 실행
CMD ["python", "-c", "print('=== SASB Container Started ==='); import os; print('PWD:', os.getcwd()); print('User:', os.getenv('USER', 'unknown')); print('Files:'); [print(f) for f in os.listdir('.')]; import time; time.sleep(30)"] 