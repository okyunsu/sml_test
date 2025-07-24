FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치 (최소한의 패키지만)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 강제 캐시 무효화 (Railway 빌드 캐시 무시)
COPY .dummyfile .dummyfile

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 강제 캐시 무효화 (shared 디렉토리용)  
COPY .dummyfile-shared ./.dummyfile-shared

# 애플리케이션 코드 및 공통 모듈 복사
COPY ./app ./app
COPY ./shared ./shared

# 시작 스크립트 복사
COPY start.sh ./
RUN chmod +x start.sh

# 업로드 디렉토리 생성
RUN mkdir -p uploads

# 디렉토리 구조 검증
RUN ls -la /app/shared || echo "❗ Warning: shared directory not found"
RUN ls -la /app/app/materiality/ || echo "Warning: materiality directory not found"

# Railway는 동적 포트 할당하므로 EXPOSE 불필요

# start.sh 실행 (절대 경로)
CMD ["/bin/bash", "/app/start.sh"] 