from fastapi import FastAPI
from app.api.news_ml_router import router as news_ml_router

app = FastAPI(
    title="Newstun ML Service",
    description="뉴스 ML 분석 서비스 - ESG 분류 및 감정 분석",
    version="1.0.0"
)

app.include_router(news_ml_router) 