import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.news_router import router as news_router

app = FastAPI(
    title="News Service",
    description="네이버 검색 API를 활용한 뉴스 수집 마이크로서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(news_router, prefix="/api/v1/news", tags=["news"])

# 대시보드 라우터 추가
from .api.dashboard_router import router as dashboard_router
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])

@app.get("/")
async def root():
    return {"message": "News Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "news-service"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True) 