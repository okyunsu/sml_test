import json
from fastapi import APIRouter, FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
import sys
from dotenv import load_dotenv
from app.domain.model.service_proxy_factory import ServiceProxyFactory
from contextlib import asynccontextmanager
from app.domain.model.request_model import NewsSearchRequest, CompanyNewsRequest, BatchNewsRequest, GenericRequest
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
    logger.info("🚀 News Gateway API 서비스 시작")
    yield
    logger.info("🛑 News Gateway API 서비스 종료")


# ✅ FastAPI 앱 생성 
app = FastAPI(
    title="News Gateway API",
    description="Gateway API for News Service",
    version="1.0.0",
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
gateway_router = APIRouter(prefix="/gateway/v1", tags=["News Gateway API"])

# ✅ 헬스 체크 엔드포인트 추가
@gateway_router.get("/health", summary="헬스 체크")
async def health_check():
    return {
        "status": "healthy",
        "service": "news-gateway",
        "version": "1.0.0",
        "target_service": "news-service"
    }

# ✅ GET 요청 프록시
@gateway_router.get("/{service}/{path:path}", summary="GET 프록시")
async def proxy_get(
    service: ServiceType, 
    path: str, 
    request: Request
):
    factory = ServiceProxyFactory(service_type=service)
    response = await factory.request(
        method="GET",
        path=path,
        headers=request.headers.raw
    )
    
    try:
        if response.headers.get("content-type", "").startswith("application/json"):
            return JSONResponse(content=response.json(), status_code=response.status_code)
        else:
            return JSONResponse(content={"data": response.text}, status_code=response.status_code)
    except:
        return JSONResponse(content={"data": response.text}, status_code=response.status_code)

# ✅ POST 요청 프록시 (뉴스 검색용)
@gateway_router.post("/{service}/search/news", summary="뉴스 검색 프록시")
async def proxy_news_search(
    service: ServiceType, 
    request_body: NewsSearchRequest,
    request: Request
):
    print(f"🔍 Received news search request for service: {service}")
    factory = ServiceProxyFactory(service_type=service)
    body = request_body.model_dump_json()
    print(f"Request body: {body}")
    
    response = await factory.request(
        method="POST",
        path="search/news",
        headers=request.headers.raw,
        body=body.encode('utf-8')
    )
    
    if response.status_code == 200:
        try:
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
        except json.JSONDecodeError:
            return JSONResponse(
                content={"detail": "⚠️Invalid JSON response from service", "raw_response": response.text},
                status_code=500
            )
    else:
        return JSONResponse(
            content={"detail": f"Service error: {response.text}"},
            status_code=response.status_code
        )

# ✅ POST 요청 프록시 (회사 뉴스 검색용)
@gateway_router.post("/{service}/search/companies/{company}", summary="회사 뉴스 검색 프록시")
async def proxy_company_news_search(
    service: ServiceType, 
    company: str,
    request: Request
):
    print(f"🏢 Received company news search request for: {company}")
    factory = ServiceProxyFactory(service_type=service)
    
    response = await factory.request(
        method="POST",
        path=f"companies/{company}",
        headers=request.headers.raw
    )
    
    if response.status_code == 200:
        try:
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
        except json.JSONDecodeError:
            return JSONResponse(
                content={"detail": "⚠️Invalid JSON response from service", "raw_response": response.text},
                status_code=500
            )
    else:
        return JSONResponse(
            content={"detail": f"Service error: {response.text}"},
            status_code=response.status_code
        )

# ✅ POST 요청 프록시 (회사 뉴스 분석용)
@gateway_router.post("/{service}/search/companies/{company}/analyze", summary="회사 뉴스 분석 프록시")
async def proxy_company_news_analysis(
    service: ServiceType, 
    company: str,
    request: Request
):
    print(f"📊 Received company analysis request for: {company}")
    factory = ServiceProxyFactory(service_type=service)
    
    response = await factory.request(
        method="POST",
        path=f"companies/{company}/analyze",
        headers=request.headers.raw
    )
    
    if response.status_code == 200:
        try:
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
        except json.JSONDecodeError:
            return JSONResponse(
                content={"detail": "⚠️Invalid JSON response from service", "raw_response": response.text},
                status_code=500
            )
    else:
        return JSONResponse(
            content={"detail": f"Service error: {response.text}"},
            status_code=response.status_code
        )

# ✅ 일반 POST 요청 프록시
@gateway_router.post("/{service}/{path:path}", summary="일반 POST 프록시")
async def proxy_post(
    service: ServiceType, 
    path: str, 
    request_body: GenericRequest,
    request: Request
):
    print(f"📮 Received POST request for service: {service}, path: {path}")
    factory = ServiceProxyFactory(service_type=service)
    body = request_body.model_dump_json()
    print(f"Request body: {body}")
    
    response = await factory.request(
        method="POST",
        path=path,
        headers=request.headers.raw,
        body=body.encode('utf-8')
    )
    
    if response.status_code == 200:
        try:
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
        except json.JSONDecodeError:
            return JSONResponse(
                content={"detail": "⚠️Invalid JSON response from service", "raw_response": response.text},
                status_code=500
            )
    else:
        return JSONResponse(
            content={"detail": f"Service error: {response.text}"},
            status_code=response.status_code
        )

# ✅ PUT 요청 프록시
@gateway_router.put("/{service}/{path:path}", summary="PUT 프록시")
async def proxy_put(service: ServiceType, path: str, request: Request):
    factory = ServiceProxyFactory(service_type=service)
    response = await factory.request(
        method="PUT",
        path=path,
        headers=request.headers.raw,
        body=await request.body()
    )
    
    try:
        if response.headers.get("content-type", "").startswith("application/json"):
            return JSONResponse(content=response.json(), status_code=response.status_code)
        else:
            return JSONResponse(content={"data": response.text}, status_code=response.status_code)
    except:
        return JSONResponse(content={"data": response.text}, status_code=response.status_code)

# ✅ DELETE 요청 프록시
@gateway_router.delete("/{service}/{path:path}", summary="DELETE 프록시")
async def proxy_delete(service: ServiceType, path: str, request: Request):
    factory = ServiceProxyFactory(service_type=service)
    response = await factory.request(
        method="DELETE",
        path=path,
        headers=request.headers.raw,
        body=await request.body()
    )
    
    try:
        if response.headers.get("content-type", "").startswith("application/json"):
            return JSONResponse(content=response.json(), status_code=response.status_code)
        else:
            return JSONResponse(content={"data": response.text}, status_code=response.status_code)
    except:
        return JSONResponse(content={"data": response.text}, status_code=response.status_code)

# ✅ PATCH 요청 프록시
@gateway_router.patch("/{service}/{path:path}", summary="PATCH 프록시")
async def proxy_patch(service: ServiceType, path: str, request: Request):
    factory = ServiceProxyFactory(service_type=service)
    response = await factory.request(
        method="PATCH",
        path=path,
        headers=request.headers.raw,
        body=await request.body()
    )
    
    try:
        if response.headers.get("content-type", "").startswith("application/json"):
            return JSONResponse(content=response.json(), status_code=response.status_code)
        else:
            return JSONResponse(content={"data": response.text}, status_code=response.status_code)
    except:
        return JSONResponse(content={"data": response.text}, status_code=response.status_code)

# ✅ 라우터 등록
app.include_router(gateway_router)

# ✅ 루트 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "News Gateway API v1.0.0",
        "description": "Gateway for News Service",
        "target_service": "news-service (localhost:8002)",
        "endpoints": {
            "health": "/gateway/v1/health",
            "news_search": "/gateway/v1/news/search/news",
            "company_search": "/gateway/v1/news/search/companies/{company}",
            "company_analysis": "/gateway/v1/news/search/companies/{company}/analyze",
            "dashboard": "/gateway/v1/news/dashboard/*",
            "system": "/gateway/v1/news/system/*",
            "docs": "/docs"
        }
    }

# ✅ 서버 실행
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 

