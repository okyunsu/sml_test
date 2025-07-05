"""의존성 주입 컨테이너"""
from typing import Optional, Dict, Any, Type, TypeVar
from abc import ABC, abstractmethod
import logging
from app.config.settings import settings, Settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyContainer:
    """의존성 주입 컨테이너"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register_singleton(self, service_key: str, instance: Any):
        """싱글톤 서비스 등록"""
        self._singletons[service_key] = instance
        logger.debug(f"싱글톤 서비스 등록: {service_key}")
    
    def register_factory(self, service_key: str, factory: callable):
        """팩토리 함수 등록"""
        self._factories[service_key] = factory
        logger.debug(f"팩토리 함수 등록: {service_key}")
    
    def register_transient(self, service_key: str, service_class: Type[T]):
        """일시적 서비스 등록"""
        self._services[service_key] = service_class
        logger.debug(f"일시적 서비스 등록: {service_key}")
    
    def get(self, service_key: str) -> Any:
        """서비스 인스턴스 반환"""
        # 싱글톤 먼저 확인
        if service_key in self._singletons:
            return self._singletons[service_key]
        
        # 팩토리 확인
        if service_key in self._factories:
            return self._factories[service_key]()
        
        # 일시적 서비스 확인
        if service_key in self._services:
            service_class = self._services[service_key]
            return service_class()
        
        raise ValueError(f"서비스를 찾을 수 없습니다: {service_key}")
    
    def get_optional(self, service_key: str) -> Optional[Any]:
        """선택적 서비스 반환"""
        try:
            return self.get(service_key)
        except ValueError:
            return None


# 전역 컨테이너 인스턴스
container = DependencyContainer()


def setup_dependencies():
    """의존성 설정"""
    from app.core.redis_client import redis_client
    from app.core.http_client import HttpClientManager
    from app.config.ml_settings import (
        ml_model_settings, ml_processing_settings, dashboard_settings
    )
    from app.domain.model.ml_loader import ModelManager
    
    # 인프라 서비스들
    container.register_singleton("redis_client", redis_client)
    container.register_factory("http_client", lambda: HttpClientManager())
    
    # 설정들
    container.register_singleton("ml_model_settings", ml_model_settings)
    container.register_singleton("ml_processing_settings", ml_processing_settings)
    container.register_singleton("dashboard_settings", dashboard_settings)
    
    # 모델 관리자
    container.register_factory("model_manager", lambda: ModelManager(ml_model_settings))
    
    # 도메인 서비스들
    from app.domain.service.news_service import NewsService
    from app.domain.service.news_analysis_service import NewsAnalysisService
    from app.domain.service.ml_inference_service import MLInferenceService
    from app.domain.service.dashboard_service import DashboardService
    from app.domain.service.analysis_workflow_service import AnalysisWorkflowService
    
    container.register_transient("news_service", NewsService)
    container.register_transient("news_analysis_service", NewsAnalysisService)
    container.register_transient("ml_inference_service", MLInferenceService)
    container.register_transient("dashboard_service", DashboardService)
    container.register_transient("analysis_workflow_service", AnalysisWorkflowService)
    
    # 컨트롤러들
    from app.domain.controller.news_controller import NewsController
    from app.domain.controller.dashboard_controller import DashboardController
    
    container.register_transient("news_controller", NewsController)
    container.register_transient("dashboard_controller", DashboardController)
    
    logger.info("의존성 주입 컨테이너 설정 완료")


def get_dependency() -> DependencyContainer:
    """의존성 컨테이너 반환"""
    return container

def get_settings() -> Settings:
    """설정 객체 반환 (FastAPI Depends 용)"""
    return settings 