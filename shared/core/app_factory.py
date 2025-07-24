"""
FastAPI 앱 팩토리
모든 마이크로서비스에서 공통으로 사용하는 FastAPI 앱 초기화 로직
"""
from typing import Dict, Any, Optional, Callable
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def create_fastapi_app(
    title: str = "API Service",
    description: str = "마이크로서비스 API",
    version: str = "1.0.0",
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
    exception_handlers: Optional[Dict[Any, Callable]] = None,
    enable_cors: bool = True,
    cors_origins: Optional[list] = None,
    server_urls: Optional[list] = None
) -> FastAPI:
    """
    FastAPI 앱을 생성하고 공통 설정을 적용합니다.
    
    Args:
        title: API 제목
        description: API 설명
        version: API 버전
        docs_url: Swagger UI URL
        redoc_url: ReDoc URL
        exception_handlers: 예외 처리 핸들러들
        enable_cors: CORS 활성화 여부
        cors_origins: 허용할 CORS origins
    
    Returns:
        설정된 FastAPI 앱 인스턴스
    """
    
    # Railway 환경에서 서버 URL 자동 감지
    import os
    if server_urls is None:
        # 1차: Railway 자동 환경변수 확인
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN") or os.getenv("RAILWAY_STATIC_URL")
        
        # 2차: 수동 설정 환경변수 확인
        swagger_url = os.getenv("SWAGGER_SERVER_URL")
        
        # 3차: 서비스별 하드코딩 (Railway 전용)
        if not railway_domain and not swagger_url:
            # Railway 환경 감지 (RAILWAY_* 환경변수 존재 확인)
            if any(key.startswith('RAILWAY_') for key in os.environ.keys()):
                # 현재 실행 중인 서비스 추론 (제목 기준)
                if "SASB" in title.upper() or "sasb" in title.lower():
                    railway_domain = "sasb-production.up.railway.app"
                elif "MATERIAL" in title.upper() or "material" in title.lower():
                    railway_domain = "material-production.up.railway.app"
        
        if railway_domain or swagger_url:
            final_url = swagger_url or f"https://{railway_domain}"
            server_urls = [
                {"url": final_url, "description": "Railway Production"}
            ]
        else:
            # 로컬 개발 환경
            server_urls = [
                {"url": "http://localhost:8000", "description": "Local Development"}
            ]
    
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        servers=server_urls
    )
    
    # CORS 미들웨어 추가 (Railway 환경 최적화)
    if enable_cors:
        # Railway와 로컬 개발 환경을 모두 지원하는 CORS 설정
        if cors_origins is None:
            cors_origins = [
                "*"  # 모든 도메인 허용 (Railway 환경에서 안전함)
            ]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=False,  # "*" origin과 함께 사용하려면 False여야 함
            allow_methods=["*"],  # 모든 메서드 허용
            allow_headers=["*"],  # 모든 헤더 허용
            expose_headers=["*"],
            max_age=86400,  # 24시간 preflight 캐시
        )
    
    # 예외 핸들러 등록
    if exception_handlers:
        for exc_type, handler in exception_handlers.items():
            app.add_exception_handler(exc_type, handler)
    
    return app 