"""공통 예외 클래스 및 에러 핸들러"""
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import traceback
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """에러 코드 열거형"""
    # 일반 에러
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    
    # 뉴스 서비스 관련
    NEWS_SEARCH_ERROR = "NEWS_SEARCH_ERROR"
    NEWS_ANALYSIS_ERROR = "NEWS_ANALYSIS_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    
    # ML 서비스 관련
    ML_MODEL_ERROR = "ML_MODEL_ERROR"
    ML_INFERENCE_ERROR = "ML_INFERENCE_ERROR"
    
    # 캐시/데이터베이스 관련
    REDIS_CONNECTION_ERROR = "REDIS_CONNECTION_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    
    # 설정/인증 관련
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"


class BaseServiceException(Exception):
    """서비스 기본 예외 클래스"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class NewsServiceException(BaseServiceException):
    """뉴스 서비스 예외"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.NEWS_SEARCH_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, cause)


class MLServiceException(BaseServiceException):
    """ML 서비스 예외"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.ML_MODEL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, cause)


class CacheException(BaseServiceException):
    """캐시 서비스 예외"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.CACHE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, cause)


class ExternalAPIException(BaseServiceException):
    """외부 API 호출 예외"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.EXTERNAL_API_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, cause)


class ErrorHandler:
    """에러 핸들러 클래스"""
    
    @staticmethod
    def handle_service_exception(exc: BaseServiceException) -> JSONResponse:
        """서비스 예외 처리"""
        logger.error(f"서비스 예외 발생: {exc.error_code.value} - {exc.message}")
        
        # 상세 로깅 (디버그 모드에서)
        if logger.isEnabledFor(logging.DEBUG):
            if exc.cause:
                logger.debug(f"원인: {exc.cause}")
            if exc.details:
                logger.debug(f"상세정보: {exc.details}")
        
        # HTTP 상태 코드 매핑
        status_code = ErrorHandler._get_http_status_code(exc.error_code)
        
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict()
        )
    
    @staticmethod
    def handle_http_exception(exc: HTTPException) -> JSONResponse:
        """HTTP 예외 처리"""
        logger.error(f"HTTP 예외 발생: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": ErrorCode.VALIDATION_ERROR.value,
                "message": exc.detail,
                "details": {},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def handle_generic_exception(exc: Exception) -> JSONResponse:
        """일반 예외 처리"""
        logger.error(f"예상치 못한 예외 발생: {type(exc).__name__} - {str(exc)}")
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                "message": "내부 서버 오류가 발생했습니다.",
                "details": {
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc)
                },
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def _get_http_status_code(error_code: ErrorCode) -> int:
        """에러 코드에 따른 HTTP 상태 코드 반환"""
        status_mapping = {
            ErrorCode.NOT_FOUND: 404,
            ErrorCode.VALIDATION_ERROR: 400,
            ErrorCode.AUTHENTICATION_ERROR: 401,
            ErrorCode.CONFIGURATION_ERROR: 400,
            ErrorCode.EXTERNAL_API_ERROR: 502,
            ErrorCode.NEWS_SEARCH_ERROR: 503,
            ErrorCode.NEWS_ANALYSIS_ERROR: 503,
            ErrorCode.ML_MODEL_ERROR: 503,
            ErrorCode.ML_INFERENCE_ERROR: 503,
            ErrorCode.REDIS_CONNECTION_ERROR: 503,
            ErrorCode.CACHE_ERROR: 503,
        }
        
        return status_mapping.get(error_code, 500)


# 전역 예외 핸들러 등록을 위한 함수들
async def service_exception_handler(request: Request, exc: BaseServiceException):
    """서비스 예외 핸들러"""
    return ErrorHandler.handle_service_exception(exc)


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러"""
    return ErrorHandler.handle_http_exception(exc)


async def generic_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    return ErrorHandler.handle_generic_exception(exc) 