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
# 🚨 app_factory.py 직접 생성 (캐시 완전 우회)
RUN echo 'from typing import Dict, Any, Optional, Callable' > ./shared/core/app_factory.py && \
    echo 'from fastapi import FastAPI, HTTPException' >> ./shared/core/app_factory.py && \
    echo 'from fastapi.middleware.cors import CORSMiddleware' >> ./shared/core/app_factory.py && \
    echo 'from fastapi.responses import JSONResponse' >> ./shared/core/app_factory.py && \
    echo 'import logging' >> ./shared/core/app_factory.py && \
    echo 'import sys' >> ./shared/core/app_factory.py && \
    echo '' >> ./shared/core/app_factory.py && \
    echo 'logging.basicConfig(' >> ./shared/core/app_factory.py && \
    echo '    level=logging.INFO,' >> ./shared/core/app_factory.py && \
    echo '    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",' >> ./shared/core/app_factory.py && \
    echo '    handlers=[logging.StreamHandler(sys.stdout)]' >> ./shared/core/app_factory.py && \
    echo ')' >> ./shared/core/app_factory.py && \
    echo '' >> ./shared/core/app_factory.py && \
    echo 'def create_fastapi_app(' >> ./shared/core/app_factory.py && \
    echo '    title: str = "API Service",' >> ./shared/core/app_factory.py && \
    echo '    description: str = "마이크로서비스 API",' >> ./shared/core/app_factory.py && \
    echo '    version: str = "1.0.0",' >> ./shared/core/app_factory.py && \
    echo '    docs_url: str = "/docs",' >> ./shared/core/app_factory.py && \
    echo '    redoc_url: str = "/redoc",' >> ./shared/core/app_factory.py && \
    echo '    exception_handlers: Optional[Dict[Any, Callable]] = None,' >> ./shared/core/app_factory.py && \
    echo '    enable_cors: bool = True,' >> ./shared/core/app_factory.py && \
    echo '    cors_origins: Optional[list] = None,' >> ./shared/core/app_factory.py && \
    echo '    server_urls: Optional[list] = None' >> ./shared/core/app_factory.py && \
    echo ') -> FastAPI:' >> ./shared/core/app_factory.py && \
    echo '    import os' >> ./shared/core/app_factory.py && \
    echo '    if server_urls is None:' >> ./shared/core/app_factory.py && \
    echo '        if "SASB" in title.upper() or "sasb" in title.lower():' >> ./shared/core/app_factory.py && \
    echo '            server_urls = [{"url": "https://sasb-production.up.railway.app", "description": "SASB Railway Production"}]' >> ./shared/core/app_factory.py && \
    echo '        elif "MATERIAL" in title.upper() or "material" in title.lower():' >> ./shared/core/app_factory.py && \
    echo '            server_urls = [{"url": "https://material-production.up.railway.app", "description": "Material Railway Production"}]' >> ./shared/core/app_factory.py && \
    echo '        else:' >> ./shared/core/app_factory.py && \
    echo '            server_urls = [{"url": "http://localhost:8000", "description": "Local Development"}]' >> ./shared/core/app_factory.py && \
    echo '    app = FastAPI(title=title, description=description, version=version, docs_url=docs_url, redoc_url=redoc_url, servers=server_urls)' >> ./shared/core/app_factory.py && \
    echo '    if enable_cors:' >> ./shared/core/app_factory.py && \
    echo '        if cors_origins is None:' >> ./shared/core/app_factory.py && \
    echo '            cors_origins = ["*"]' >> ./shared/core/app_factory.py && \
    echo '        app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"], expose_headers=["*"], max_age=86400)' >> ./shared/core/app_factory.py && \
    echo '    if exception_handlers:' >> ./shared/core/app_factory.py && \
    echo '        for exc_type, handler in exception_handlers.items():' >> ./shared/core/app_factory.py && \
    echo '            app.add_exception_handler(exc_type, handler)' >> ./shared/core/app_factory.py && \
    echo '    return app' >> ./shared/core/app_factory.py
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