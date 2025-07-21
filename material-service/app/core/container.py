"""
Material Service 의존성 주입 컨테이너
공통 DI 컨테이너를 상속하여 Material 서비스 전용 의존성 구성
"""
import logging
from shared.core.dependency_container import BaseContainer

logger = logging.getLogger(__name__)

class MaterialServiceContainer(BaseContainer):
    """Material 서비스 전용 의존성 컨테이너"""
    
    def setup_dependencies(self) -> None:
        """Material 서비스 의존성 설정 (단순화)"""
        from app.config.settings import get_settings
        
        settings = get_settings()
        
        # === 1. Core Infrastructure ===
        # Settings (싱글톤)
        self.registry.register_instance("settings", settings)
        
        logger.info("🎯 Material Service 의존성 설정 완료")
    
    def get_analysis_service(self):
        """편의 메서드: Analysis Service 조회"""
        from app.domain.service.materiality_analysis_service import MaterialityAnalysisService
        return self.get_typed("analysis_service", MaterialityAnalysisService)
    
    def get_gateway_client(self):
        """편의 메서드: Gateway Client 조회"""
        from app.core.gateway_client import GatewayClient
        return self.get_typed("gateway_client", GatewayClient)

# 전역 컨테이너 인스턴스
_material_container = None

def get_material_container() -> MaterialServiceContainer:
    """Material 서비스 컨테이너 조회"""
    global _material_container
    if _material_container is None:
        _material_container = MaterialServiceContainer()
        
        # 전역 컨테이너로도 설정
        from shared.core.dependency_container import set_container
        set_container(_material_container)
    
    return _material_container

def initialize_material_container() -> MaterialServiceContainer:
    """Material 서비스 컨테이너 초기화"""
    container = get_material_container()
    container.ensure_setup()
    
    logger.info("🚀 Material Service DI 컨테이너 초기화 완료")
    return container 