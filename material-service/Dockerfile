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

# 🚨 RAILWAY 캐시 완전 무효화 🚨
# 모든 후속 레이어 강제 재빌드
ARG CACHE_BUST=2025-07-24-03:50:00
RUN echo "CACHE_BUST=${CACHE_BUST}" > /tmp/cache_bust.txt

# 강제 캐시 무효화 (shared 디렉토리용)  
COPY .dummyfile-shared ./.dummyfile-shared

# 🚨 SHARED 디렉토리 강제 캐시 무효화 🚨
# 개별 파일 복사로 캐시 회피
# 🚨 Material Service: 간단한 COPY 방식 (SASB는 이미 성공)
# 더미 파일로 캐시 무효화만 적용
COPY ./shared/core/redis_factory.py ./shared/core/redis_factory.py
COPY ./shared/core/__init__.py ./shared/core/__init__.py
COPY ./shared/core/app_factory.py ./shared/core/app_factory.py
COPY ./shared/core/dependency_container.py ./shared/core/dependency_container.py
COPY ./shared/core/exception_handlers.py ./shared/core/exception_handlers.py
COPY ./shared/config/ ./shared/config/
COPY ./shared/services/ ./shared/services/
COPY ./shared/interfaces/ ./shared/interfaces/
COPY ./shared/docs/ ./shared/docs/
COPY ./shared/testing/ ./shared/testing/
COPY ./shared/__init__.py ./shared/__init__.py
RUN echo "✅ material service shared 개별 파일 복사 완료: $(date)" > ./shared_copy_timestamp.txt

# 애플리케이션 코드 복사
COPY ./app ./app

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