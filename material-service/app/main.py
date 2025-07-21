import uvicorn
import logging
import os
import sys

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# ✅ 공통 모듈 사용
from shared.core.app_factory import create_fastapi_app
from shared.core.exception_handlers import DEFAULT_EXCEPTION_HANDLERS

from .api.materiality_router import materiality_router

# 로깅 설정 (공통 모듈에서 처리)
logger = logging.getLogger(__name__)

# ✅ FastAPI 앱 생성 (공통 팩토리 사용)
app = create_fastapi_app(
    title="Material Assessment Service",
    description="중대성 평가 동향 분석 및 업데이트 제안 서비스",
    version="1.0.0",
    exception_handlers=DEFAULT_EXCEPTION_HANDLERS
)

# 라우터 등록
app.include_router(materiality_router)

@app.get("/")
async def root():
    return {
        "message": "Material Assessment Service",
        "status": "running",
        "version": "1.0.0",
        "description": "중대성 평가 동향 분석 및 업데이트 제안 서비스",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "material-assessment-service",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,  # sasb-service(8003)과 구분
        reload=True
    ) 