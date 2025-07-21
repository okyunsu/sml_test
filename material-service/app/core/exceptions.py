from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Union
import logging

logger = logging.getLogger(__name__)

class BaseServiceException(Exception):
    """기본 서비스 예외"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class FileParsingException(BaseServiceException):
    """파일 파싱 예외"""
    def __init__(self, message: str):
        super().__init__(message, 400)

class DataValidationException(BaseServiceException):
    """데이터 검증 예외"""
    def __init__(self, message: str):
        super().__init__(message, 422)

class MappingException(BaseServiceException):
    """매핑 예외"""
    def __init__(self, message: str):
        super().__init__(message, 400)

class AnalysisException(BaseServiceException):
    """분석 예외"""
    def __init__(self, message: str):
        super().__init__(message, 500)

# 예외 핸들러들
async def service_exception_handler(request: Request, exc: BaseServiceException):
    """서비스 예외 핸들러"""
    logger.error(f"Service exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": "service_error",
            "status_code": exc.status_code
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러"""
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "type": "http_error",
            "status_code": exc.status_code
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "type": "internal_error",
            "status_code": 500
        }
    ) 