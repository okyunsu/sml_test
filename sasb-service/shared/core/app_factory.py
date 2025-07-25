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
    cors_origins: list = ["*"]
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
    
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url=docs_url,
        redoc_url=redoc_url
    )
    
    # CORS 미들웨어 추가
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 예외 핸들러 등록
    if exception_handlers:
        for exc_type, handler in exception_handlers.items():
            app.add_exception_handler(exc_type, handler)
    
    return app 