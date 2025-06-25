from fastapi import FastAPI
from app.api.esg_tuning_router import router as esg_tuning_router
from app.api.gri_router import router as gri_router

app = FastAPI(
    title="ESG Fine-tuning Service",
    description="ESG 보고서 기반 허깅페이스 트랜스포머 파인튜닝 서비스",
    version="2.0.0-rtx2080"
)

app.include_router(esg_tuning_router)
app.include_router(gri_router) 