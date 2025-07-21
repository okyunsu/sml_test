from typing import Dict, Any
import os
import sys

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

# ✅ 공통 Redis 팩토리 사용
from shared.core.redis_factory import RedisClientFactory

from ..domain.service.sasb_service import SASBService
from ..domain.service.analysis_service import AnalysisService
from ..domain.service.naver_news_service import NaverNewsService
from ..domain.service.ml_inference_service import MLInferenceService
from ..domain.controller.sasb_controller import SASBController
from ..domain.controller.dashboard_controller import DashboardController
from ..config.settings import settings

class DependencyContainer:
    """의존성 주입 컨테이너 - 올바른 의존성 주입 순서 보장"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """서비스 초기화 - 의존성 순서에 따라 초기화"""
        # 1. 인프라 계층 (가장 기본) - 공통 Redis 팩토리 사용
        redis_client = RedisClientFactory.create_from_url(settings.CELERY_BROKER_URL)
        
        # 2. 기본 서비스 계층 (의존성 없음)
        naver_news_service = NaverNewsService()
        ml_inference_service = MLInferenceService()
        
        # 3. 중간 서비스 계층 (기본 서비스들에 의존)
        analysis_service = AnalysisService()
        
        # 4. 고수준 서비스 계층 (다른 서비스들에 의존)
        sasb_service = SASBService()
        
        # 5. 컨트롤러 계층 (서비스들에 의존)
        sasb_controller = SASBController()
        dashboard_controller = DashboardController()
        
        # 컨테이너에 등록
        self._services.update({
            "redis_client": redis_client,
            "naver_news_service": naver_news_service,
            "ml_inference_service": ml_inference_service,
            "analysis_service": analysis_service,
            "sasb_service": sasb_service,
            "sasb_controller": sasb_controller,
            "dashboard_controller": dashboard_controller
        })
    
    def get(self, service_name: str) -> Any:
        """서비스 조회"""
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found in container")
        return self._services[service_name]

# Global container
container = DependencyContainer()

def get_dependency() -> DependencyContainer:
    """의존성 주입 컨테이너 반환"""
    return container

def get_sasb_service() -> SASBService:
    """SASBService 반환 (하위 호환성)"""
    return container.get("sasb_service")

def get_analysis_service() -> AnalysisService:
    """AnalysisService 반환"""
    return container.get("analysis_service")

def get_redis_client():
    """Redis 클라이언트 반환"""
    return container.get("redis_client") 