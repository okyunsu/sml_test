import json
from typing import Optional
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
import sys
from dotenv import load_dotenv
from app.domain.model.service_proxy_factory import ServiceProxyFactory
from contextlib import asynccontextmanager
from app.domain.model.service_type import ServiceType

# ✅로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("gateway_api")

# ✅ .env 파일 로드
load_dotenv()

# ✅ 애플리케이션 시작 시 실행
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 News Gateway API 서비스 시작 (Dynamic Proxy)")
    yield
    logger.info("🛑 News Gateway API 서비스 종료")

# ✅ FastAPI 앱 생성 
app = FastAPI(
    title="News Gateway API - Dynamic Proxy",
    description="동적 프록시 기반 Gateway API",
    version="3.0.0-dynamic",
    lifespan=lifespan
)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 메인 라우터 생성
gateway_router = APIRouter(prefix="/gateway/v1", tags=["Dynamic Proxy Gateway"])

# ============================================================================
# 🎯 기본 기능 (헬스체크 & 디버그)
# ============================================================================

@gateway_router.get("/health", summary="Gateway 헬스체크")
async def gateway_health():
    """Gateway 헬스체크"""
    return {
        "status": "healthy",
        "service": "news-gateway",
        "version": "3.0.0-dynamic",
        "target_service": "news-service",
        "proxy_type": "dynamic"
    }

@gateway_router.get("/debug/connection", summary="연결 테스트")
async def debug_connection():
    """News Service 연결 상태 테스트"""
    import httpx
    
    news_service_url = "http://news-service:8002"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{news_service_url}/health")
            return {
                "status": "success",
                "news_service": {
                    "url": news_service_url,
                    "status_code": response.status_code,
                    "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
            }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__
        }

# ============================================================================
# 🌐 동적 프록시 시스템 (모든 HTTP 메서드 지원)
# ============================================================================

async def handle_proxy_request(
    service: ServiceType,
    path: str,
    method: str,
    request: Request
):
    """통합 프록시 요청 처리"""
    try:
        logger.info(f"🔄 프록시 요청: {method} /{service.value}/{path}")
        
        factory = ServiceProxyFactory(service_type=service)
        
        # 요청 본문 준비
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body_data = await request.json()
                body = json.dumps(body_data).encode('utf-8')
            except:
                body = await request.body()
        
        # API 요청 실행
        response = await factory.request(
            method=method,
            path=path,
            headers=request.headers.raw,
            body=body
        )
        
        # 응답 처리
        if response.status_code >= 200 and response.status_code < 300:
            try:
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code
                )
            except json.JSONDecodeError:
                return JSONResponse(
                    content={"message": response.text, "raw_response": True},
                    status_code=response.status_code
                )
        else:
            return JSONResponse(
                content={"detail": f"서비스 오류: {response.text}"},
                status_code=response.status_code
            )
            
    except Exception as e:
        logger.error(f"프록시 요청 실패: {str(e)}")
        return JSONResponse(
            content={"detail": f"프록시 요청 중 오류: {str(e)}"},
            status_code=500
        )

# ============================================================================
# 🔄 동적 프록시 엔드포인트들 (모든 HTTP 메서드)
# ============================================================================

@gateway_router.get("/{service}/{path:path}", summary="동적 GET 프록시")
async def proxy_get(service: ServiceType, path: str, request: Request):
    """동적 GET 요청 프록시"""
    return await handle_proxy_request(service, path, "GET", request)

@gateway_router.post("/{service}/{path:path}", summary="동적 POST 프록시")
async def proxy_post(service: ServiceType, path: str, request: Request):
    """동적 POST 요청 프록시"""
    return await handle_proxy_request(service, path, "POST", request)

@gateway_router.put("/{service}/{path:path}", summary="동적 PUT 프록시")
async def proxy_put(service: ServiceType, path: str, request: Request):
    """동적 PUT 요청 프록시"""
    return await handle_proxy_request(service, path, "PUT", request)

@gateway_router.delete("/{service}/{path:path}", summary="동적 DELETE 프록시")
async def proxy_delete(service: ServiceType, path: str, request: Request):
    """동적 DELETE 요청 프록시"""
    return await handle_proxy_request(service, path, "DELETE", request)

@gateway_router.patch("/{service}/{path:path}", summary="동적 PATCH 프록시")
async def proxy_patch(service: ServiceType, path: str, request: Request):
    """동적 PATCH 요청 프록시"""
    return await handle_proxy_request(service, path, "PATCH", request)

# ✅ 라우터 등록
app.include_router(gateway_router)

# ✅ 루트 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "News Gateway API v3.0.0 - Dynamic Proxy",
        "description": "동적 프록시 기반 Gateway - 모든 요청을 자동으로 news-service로 전달",
        "architecture": "dynamic-proxy",
        "supported_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "usage": {
            "pattern": "/gateway/v1/{service}/{path}",
            "example": "/gateway/v1/news/api/search",
            "service_options": ["news"]
        },
        "endpoints": {
            "health": "/gateway/v1/health",
            "debug": "/gateway/v1/debug/connection",
            "docs": "/docs"
        },
        "service_status": "healthy"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 

