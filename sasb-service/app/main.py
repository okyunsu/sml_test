from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.api.unified_router import frontend_router, dashboard_router, cache_router, system_router, worker_router
from app.core.exceptions import service_exception_handler, http_exception_handler, generic_exception_handler, BaseServiceException
from fastapi import HTTPException

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="SASB Analysis Service",
    description="SASB 프레임워크 기반 ESG 뉴스 분석 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 예외 핸들러 등록
app.add_exception_handler(BaseServiceException, service_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 라우터 등록
app.include_router(frontend_router)
app.include_router(dashboard_router)
app.include_router(cache_router)
app.include_router(system_router)
app.include_router(worker_router)

@app.get("/")
async def root():
    return {
        "message": "SASB Analysis Service",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "sasb-analysis-service",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    ) 