from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class BaseServiceException(Exception):
    """Base exception for this service."""
    def __init__(self, detail: str, status_code: int = 500):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)

class NotFoundException(BaseServiceException):
    """Exception for resources not found."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, status_code=404)

class MLServiceException(BaseServiceException):
    """Exception for ML service communication errors."""
    def __init__(self, detail: str = "Error communicating with ML service"):
        super().__init__(detail, status_code=503)

async def service_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, BaseServiceException):
        logger.error(f"Service error occurred: {exc.detail}", exc_info=True)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    return await generic_exception_handler(request, exc)


async def http_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        logger.error(f"HTTP error occurred: {exc.detail}", exc_info=True)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    return await generic_exception_handler(request, exc)

async def generic_exception_handler(request: Request, exc: Exception):
    logger.critical("An unexpected error occurred.", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    ) 