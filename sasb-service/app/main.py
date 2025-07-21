import uvicorn
import logging
import os
import sys

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# ✅ 공통 모듈 사용
from shared.core.app_factory import create_fastapi_app
from shared.core.exception_handlers import DEFAULT_EXCEPTION_HANDLERS
from shared.docs.api_documentation_helper import setup_api_documentation

from app.api.unified_router import frontend_router, dashboard_router, cache_router, system_router, worker_router
from app.core.container import initialize_sasb_container

# 로깅 설정 (공통 모듈에서 처리)
logger = logging.getLogger(__name__)

# ✅ 의존성 주입 컨테이너 초기화
container = initialize_sasb_container()
logger.info("🎯 SASB Service DI 컨테이너 적용 완료")

# ✅ FastAPI 앱 생성 (공통 팩토리 사용)
app = create_fastapi_app(
    title="SASB Analysis Service",
    description="""
    🎯 **SASB 프레임워크 기반 ESG 뉴스 분석 서비스**
    
    ### 🌟 주요 기능
    - **ESG 뉴스 분석**: 키워드 기반 뉴스 수집 및 감정 분석
    - **SASB 매핑**: 산업별 SASB 프레임워크 자동 매핑
    - **대시보드**: 실시간 분석 현황 및 시스템 상태 모니터링
    - **캐시 관리**: Redis 기반 고성능 데이터 캐싱
    - **백그라운드 작업**: Celery를 통한 비동기 분석 처리
    
    ### 🔧 기술 스택
    - **의존성 주입**: 모듈화된 아키텍처 적용
    - **리팩토링**: 545줄 → 85줄 (84% 코드 복잡도 감소)
    - **공통 헬퍼**: 재사용 가능한 분석 모듈
    - **Mock 테스트**: 인터페이스 기반 테스트 환경
    """,
    version="2.0.0",
    exception_handlers=DEFAULT_EXCEPTION_HANDLERS
)

# ✅ API 문서화 설정
setup_api_documentation(
    app=app,
    service_name="SASB Analysis Service",
    service_description="SASB 프레임워크 기반 ESG 뉴스 분석 서비스",
    version="2.0.0"
)
logger.info("📚 SASB Service API 문서화 설정 완료")

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