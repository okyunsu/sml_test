from fastapi import FastAPI
from .api.unified_router import main_router, legacy_router
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
    title="뉴스 서비스 API v3.0",
    description="간단한 구조 + 스마트 캐시 + 대시보드 + 시스템 관리",
    version="3.0.0"
)

# 글로벌 예외 핸들러 등록
app.add_exception_handler(BaseServiceException, service_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 의존성 주입 컨테이너 설정
setup_dependencies()
logger.info("의존성 주입 컨테이너 초기화 완료")

# 라우터 등록
app.include_router(main_router, tags=["Simple API"])        # 간단한 구조
app.include_router(legacy_router, tags=["Legacy API v1"])   # 기존 호환성

@app.get("/")
async def root():
    return {
        "message": "뉴스 서비스 API v3.0.0 - 간단한 구조 + 스마트 캐시",
        "features": [
            "🚀 간단한 API 구조 (Gateway 최적화)",
            "🔍 스마트 검색 (캐시 우선 → 실시간 폴백)",
            "📊 대시보드 모니터링 (백그라운드 데이터)",
            "🛠️ 시스템 관리 (헬스체크, 테스트)",
            "⚡ Redis 캐시 최적화",
            "🏗️ Clean Architecture + 의존성 주입"
        ],
        "api_structures": {
            "simple": {
                "description": "Gateway 최적화된 간단한 구조",
                "examples": [
                    "/search",
                    "/companies/{company}",
                    "/dashboard/status",
                    "/cache/info",
                    "/system/health"
                ]
            },
            "legacy": {
                "description": "기존 호환성을 위한 구조",
                "examples": [
                    "/api/v1/search",
                    "/api/v1/companies/{company}",
                    "/api/v1/dashboard/status"
                ]
            }
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "3.0.0",
        "architecture": "Simple Structure + Clean Architecture with DI"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 