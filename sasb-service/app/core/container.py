"""
SASB Service 의존성 주입 컨테이너
공통 DI 컨테이너를 상속하여 SASB 서비스 전용 의존성 구성
"""
import logging
from shared.core.dependency_container import BaseContainer
from shared.core.redis_factory import RedisClientFactory

logger = logging.getLogger(__name__)

class SASBServiceContainer(BaseContainer):
    """SASB 서비스 전용 의존성 컨테이너"""
    
    def setup_dependencies(self) -> None:
        """SASB 서비스 의존성 설정 (단순화)"""
        from app.config.settings import get_settings
        
        settings = get_settings()
        
        # === 1. Core Infrastructure ===
        # Settings (싱글톤)
        self.registry.register_instance("settings", settings)
        
        # Redis Client (싱글톤)
        self.registry.register_singleton(
            "redis_client",
            lambda: RedisClientFactory.create_from_url(settings.REDIS_URL)
        )
        
        logger.info("🎯 SASB Service 의존성 설정 완료")
    
    def get_analysis_service(self):
        """편의 메서드: Analysis Service 조회"""
        from app.domain.service.analysis_service import AnalysisService
        return self.get_typed("analysis_service", AnalysisService)
    
    def get_sasb_service(self):
        """편의 메서드: SASB Service 조회"""
        from app.domain.service.sasb_service import SASBService
        return self.get_typed("sasb_service", SASBService)
    
    def get_redis_client(self):
        """편의 메서드: Redis Client 조회"""
        return self.get("redis_client")

# 전역 컨테이너 인스턴스
_sasb_container = None

def get_sasb_container() -> SASBServiceContainer:
    """SASB 서비스 컨테이너 조회"""
    global _sasb_container
    if _sasb_container is None:
        _sasb_container = SASBServiceContainer()
        
        # 전역 컨테이너로도 설정
        from shared.core.dependency_container import set_container
        set_container(_sasb_container)
    
    return _sasb_container

def initialize_sasb_container() -> SASBServiceContainer:
    """SASB 서비스 컨테이너 초기화"""
    container = get_sasb_container()
    container.ensure_setup()
    
    logger.info("🚀 SASB Service DI 컨테이너 초기화 완료")
    return container 