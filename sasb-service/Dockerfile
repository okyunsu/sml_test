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

# 강제 캐시 무효화 (Railway 빌드 캐시 무시)
COPY .dummyfile .dummyfile

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

# 🚨 RAILWAY 캐시 완전 무효화 🚨
# 모든 후속 레이어 강제 재빌드
ARG CACHE_BUST=2025-07-24-08:00:00
RUN echo "CACHE_BUST=${CACHE_BUST}" > /tmp/cache_bust.txt

# 강제 캐시 무효화 (shared 디렉토리용)
COPY .dummyfile-shared /home/appuser/app/.dummyfile-shared

# 🚨 SHARED 디렉토리 강제 캐시 무효화 🚨
# 개별 파일 복사로 캐시 회피
RUN mkdir -p /home/appuser/app/shared/core /home/appuser/app/shared/config /home/appuser/app/shared/services /home/appuser/app/shared/interfaces /home/appuser/app/shared/docs /home/appuser/app/shared/testing
# 🚨 redis_factory.py 강제 덮어쓰기 (캐시 완전 우회)
RUN echo 'import os' > /home/appuser/app/shared/core/redis_factory.py && \
    echo 'import logging' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo 'from typing import Optional' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo 'from urllib.parse import urlparse' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo 'import redis' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo 'logger = logging.getLogger(__name__)' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo 'class RedisClientFactory:' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '    @staticmethod' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '    def create_from_url(' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '        redis_url: Optional[str] = None,' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '        default_host: str = "localhost",' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '        default_port: int = 6379,' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '        default_db: int = 0' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '    ) -> redis.Redis:' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '        if not redis_url:' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            redis_url = os.getenv("REDIS_URL", f"redis://{default_host}:{default_port}/{default_db}")' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '        try:' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            client = redis.from_url(' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '                redis_url,' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '                decode_responses=True,' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '                socket_timeout=5,' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '                socket_connect_timeout=5,' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '                retry_on_timeout=True' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            )' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            client.ping()' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            parsed_url = urlparse(redis_url)' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            db_num = parsed_url.path[1:] if parsed_url.path and parsed_url.path[1:] else "0"' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            logger.info(f"✅ Redis 연결 성공: {parsed_url.hostname}:{parsed_url.port}/{db_num}")' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            return client' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '        except Exception as e:' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            logger.error(f"❌ Redis 연결 실패: {str(e)}")' >> /home/appuser/app/shared/core/redis_factory.py && \
    echo '            raise' >> /home/appuser/app/shared/core/redis_factory.py
COPY ./shared/core/__init__.py /home/appuser/app/shared/core/__init__.py
# 🚨 app_factory.py 직접 생성 (캐시 완전 우회)
RUN echo 'from typing import Dict, Any, Optional, Callable' > /home/appuser/app/shared/core/app_factory.py && \
    echo 'from fastapi import FastAPI, HTTPException' >> /home/appuser/app/shared/core/app_factory.py && \
    echo 'from fastapi.middleware.cors import CORSMiddleware' >> /home/appuser/app/shared/core/app_factory.py && \
    echo 'from fastapi.responses import JSONResponse' >> /home/appuser/app/shared/core/app_factory.py && \
    echo 'import logging' >> /home/appuser/app/shared/core/app_factory.py && \
    echo 'import sys' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '' >> /home/appuser/app/shared/core/app_factory.py && \
    echo 'logging.basicConfig(' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    level=logging.INFO,' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    handlers=[logging.StreamHandler(sys.stdout)]' >> /home/appuser/app/shared/core/app_factory.py && \
    echo ')' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '' >> /home/appuser/app/shared/core/app_factory.py && \
    echo 'def create_fastapi_app(' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    title: str = "API Service",' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    description: str = "마이크로서비스 API",' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    version: str = "1.0.0",' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    docs_url: str = "/docs",' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    redoc_url: str = "/redoc",' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    exception_handlers: Optional[Dict[Any, Callable]] = None,' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    enable_cors: bool = True,' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    cors_origins: Optional[list] = None,' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    server_urls: Optional[list] = None' >> /home/appuser/app/shared/core/app_factory.py && \
    echo ') -> FastAPI:' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    import os' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    if server_urls is None:' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '        if "SASB" in title.upper() or "sasb" in title.lower():' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '            server_urls = [{"url": "https://sasb-production.up.railway.app", "description": "SASB Railway Production"}]' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '        elif "MATERIAL" in title.upper() or "material" in title.lower():' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '            server_urls = [{"url": "https://material-production.up.railway.app", "description": "Material Railway Production"}]' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '        else:' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '            server_urls = [{"url": "http://localhost:8000", "description": "Local Development"}]' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    app = FastAPI(title=title, description=description, version=version, docs_url=docs_url, redoc_url=redoc_url, servers=server_urls)' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    if enable_cors:' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '        if cors_origins is None:' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '            cors_origins = ["*"]' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '        app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"], expose_headers=["*"], max_age=86400)' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    if exception_handlers:' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '        for exc_type, handler in exception_handlers.items():' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '            app.add_exception_handler(exc_type, handler)' >> /home/appuser/app/shared/core/app_factory.py && \
    echo '    return app' >> /home/appuser/app/shared/core/app_factory.py
COPY ./shared/core/dependency_container.py /home/appuser/app/shared/core/dependency_container.py
COPY ./shared/core/exception_handlers.py /home/appuser/app/shared/core/exception_handlers.py
COPY ./shared/config/ /home/appuser/app/shared/config/
COPY ./shared/services/ /home/appuser/app/shared/services/
COPY ./shared/interfaces/ /home/appuser/app/shared/interfaces/
COPY ./shared/docs/ /home/appuser/app/shared/docs/
COPY ./shared/testing/ /home/appuser/app/shared/testing/
COPY ./shared/__init__.py /home/appuser/app/shared/__init__.py
RUN echo "✅ shared 개별 파일 복사 완료: $(date)" > /home/appuser/app/shared_copy_timestamp.txt

# 애플리케이션 코드 복사
COPY ./app /home/appuser/app/app
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