from fastapi import FastAPI
from .api.unified_router import main_router
from .core.dependencies import setup_dependencies
from .core.exceptions import (
    BaseServiceException, service_exception_handler,
    http_exception_handler, generic_exception_handler
)
from fastapi import HTTPException
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="뉴스 서비스 API v2.0",
    description="스마트 검색 (캐시 우선) + 대시보드 모니터링 + 시스템 관리 - 통합 라우터",
    version="2.0.0"
)

# 글로벌 예외 핸들러 등록
app.add_exception_handler(BaseServiceException, service_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 의존성 주입 컨테이너 설정
setup_dependencies()
logger.info("의존성 주입 컨테이너 초기화 완료")

# 통합 라우터 등록
app.include_router(main_router, tags=["API v2.0"])

@app.get("/")
async def root():
    return {
        "message": "뉴스 서비스 API v2.0.0 - 통합 라우터 + 스마트 캐시",
        "features": [
            "🔍 스마트 검색 (캐시 우선 → 실시간 폴백)",
            "📊 대시보드 모니터링 (백그라운드 데이터)",
            "🛠️ 시스템 관리 (헬스체크, 테스트)",
            "⚡ Redis 캐시 최적화",
            "🏗️ Clean Architecture + 의존성 주입"
        ],
        "api_endpoints": {
            "search": "/api/v1/search/*",
            "dashboard": "/api/v1/dashboard/*", 
            "system": "/api/v1/system/*",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "2.0.0",
        "architecture": "Clean Architecture with DI"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 