"""
공통 예외 처리 핸들러
모든 마이크로서비스에서 사용하는 표준화된 예외 처리
"""
from typing import Dict, Any, Callable, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class BaseServiceException(Exception):
    """기본 서비스 예외 클래스"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(BaseServiceException):
    """검증 실패 예외"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)

class NotFoundServiceException(BaseServiceException):
    """리소스를 찾을 수 없음 예외"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, details)

class ExternalServiceException(BaseServiceException):
    """외부 서비스 호출 실패 예외"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 502, details)

async def service_exception_handler(request: Request, exc: BaseServiceException):
    """커스텀 서비스 예외 핸들러"""
    logger.error(f"Service exception: {exc.message}", extra={
        "status_code": exc.status_code,
        "details": exc.details,
        "path": str(request.url)
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """FastAPI HTTPException 핸들러"""
    logger.warning(f"HTTP exception: {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": str(request.url)
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.exception(f"Unhandled exception: {str(exc)}", extra={
        "path": str(request.url),
        "exception_type": type(exc).__name__
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "내부 서버 오류가 발생했습니다.",
            "status_code": 500,
            "path": str(request.url)
        }
    )

# 기본 예외 핸들러 매핑
DEFAULT_EXCEPTION_HANDLERS: Dict[Any, Callable] = {
    BaseServiceException: service_exception_handler,
    HTTPException: http_exception_handler,
    Exception: generic_exception_handler
} 