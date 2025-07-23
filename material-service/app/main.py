import uvicorn
import logging
import os
import sys

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ✅ 공통 모듈 사용
from shared.core.app_factory import create_fastapi_app
from shared.core.exception_handlers import DEFAULT_EXCEPTION_HANDLERS
from shared.docs.api_documentation_helper import setup_api_documentation

from .api.materiality_router import materiality_router
from .core.container import initialize_material_container

# 로깅 설정 (공통 모듈에서 처리)
logger = logging.getLogger(__name__)

# ✅ 의존성 주입 컨테이너 초기화
container = initialize_material_container()
logger.info("🎯 Material Service DI 컨테이너 적용 완료")

# ✅ FastAPI 앱 생성 (공통 팩토리 사용)
app = create_fastapi_app(
    title="Material Assessment Service",
    description="""
    🎯 **중대성 평가 동향 분석 및 업데이트 제안 서비스**
    
    ### 🌟 주요 기능
    - **중대성 분석**: 기업별 중대성 평가 변화 동향 분석
    - **파일 관리**: 중대성 평가 데이터 업로드 및 파싱
    - **추천 시스템**: AI 기반 중대성 이슈 우선순위 제안
    - **산업 분석**: 업종별 중대성 이슈 벤치마킹
    
    ### 🔧 기술 혁신
    - **리팩토링**: 266줄 거대 함수 → 30줄 (89% 감소)
    - **공통 헬퍼**: MaterialityAnalysisHelper 활용
    - **의존성 주입**: 모듈화된 서비스 아키텍처
    - **에러 처리**: 통합 에러 핸들링 시스템
    """,
    version="2.0.0",
    exception_handlers=DEFAULT_EXCEPTION_HANDLERS
)

# ✅ API 문서화 설정
setup_api_documentation(
    app=app,
    service_name="Material Assessment Service",
    service_description="중대성 평가 동향 분석 및 업데이트 제안 서비스",
    version="2.0.0"
)
logger.info("📚 Material Service API 문서화 설정 완료")

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