from typing import Dict, Any, Type, TypeVar, Optional, Callable
from abc import ABC, abstractmethod
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DependencyRegistry:
    """의존성 등록 및 관리"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._initialized = False
    
    def register_instance(self, name: str, instance: Any) -> None:
        """인스턴스 직접 등록"""
        self._services[name] = instance
        logger.debug(f"✅ 서비스 인스턴스 등록: {name}")
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """팩토리 함수 등록 (호출할 때마다 새 인스턴스)"""
        self._factories[name] = factory
        logger.debug(f"✅ 서비스 팩토리 등록: {name}")
    
    def register_singleton(self, name: str, factory: Callable) -> None:
        """싱글톤 팩토리 등록 (한 번만 생성)"""
        self._factories[name] = factory
        self._singletons[name] = None  # 지연 초기화
        logger.debug(f"✅ 싱글톤 서비스 등록: {name}")
    
    def get(self, name: str) -> Any:
        """서비스 조회"""
        # 1. 직접 등록된 인스턴스 확인
        if name in self._services:
            return self._services[name]
        
        # 2. 싱글톤 확인
        if name in self._singletons:
            if self._singletons[name] is None:
                logger.debug(f"🏭 싱글톤 생성: {name}")
                self._singletons[name] = self._factories[name]()
            return self._singletons[name]
        
        # 3. 팩토리로 새 인스턴스 생성
        if name in self._factories:
            logger.debug(f"🏭 새 인스턴스 생성: {name}")
            return self._factories[name]()
        
        # 4. 없으면 에러
        available = list(self._services.keys()) + list(self._factories.keys())
        raise ValueError(f"Service '{name}' not found. Available: {available}")
    
    def has(self, name: str) -> bool:
        """서비스 존재 여부 확인"""
        return (name in self._services or 
                name in self._factories or 
                name in self._singletons)
    
    def list_services(self) -> Dict[str, str]:
        """등록된 모든 서비스 목록"""
        services = {}
        
        for name in self._services:
            services[name] = "instance"
        
        for name in self._factories:
            if name in self._singletons:
                services[name] = "singleton"
            else:
                services[name] = "factory"
        
        return services

class BaseContainer(ABC):
    """의존성 컨테이너 기본 클래스"""
    
    def __init__(self):
        self.registry = DependencyRegistry()
        self._setup_complete = False
    
    @abstractmethod
    def setup_dependencies(self) -> None:
        """의존성 설정 (각 서비스에서 구현)"""
        pass
    
    def ensure_setup(self) -> None:
        """설정이 완료되었는지 확인하고, 필요시 실행"""
        if not self._setup_complete:
            logger.info("🔧 의존성 컨테이너 설정 시작")
            self.setup_dependencies()
            self._setup_complete = True
            logger.info("✅ 의존성 컨테이너 설정 완료")
    
    def get(self, service_name: str) -> Any:
        """서비스 조회"""
        self.ensure_setup()
        return self.registry.get(service_name)
    
    def get_typed(self, service_name: str, service_type: Type[T]) -> T:
        """타입 힌트가 있는 서비스 조회"""
        service = self.get(service_name)
        if not isinstance(service, service_type):
            raise TypeError(f"Service '{service_name}' is not of type {service_type}")
        return service

# 전역 컨테이너 인스턴스 (각 서비스에서 설정)
_global_container: Optional[BaseContainer] = None

def get_container() -> BaseContainer:
    """전역 컨테이너 조회"""
    if _global_container is None:
        raise RuntimeError("Container not initialized. Call set_container() first.")
    return _global_container

def set_container(container: BaseContainer) -> None:
    """전역 컨테이너 설정"""
    global _global_container
    _global_container = container
    logger.info(f"🌐 전역 컨테이너 설정: {container.__class__.__name__}")

# FastAPI 의존성 주입용 함수들
def get_service(service_name: str):
    """FastAPI 의존성으로 사용할 서비스 조회 함수"""
    def _get_service():
        return get_container().get(service_name)
    return _get_service

def get_typed_service(service_name: str, service_type: Type[T]):
    """타입 힌트가 있는 FastAPI 의존성 함수"""
    def _get_typed_service() -> T:
        return get_container().get_typed(service_name, service_type)
    return _get_typed_service

# 서비스별 컨테이너 예시 (각 서비스에서 상속하여 구현)
class StandardServiceContainer(BaseContainer):
    """표준 서비스를 위한 기본 컨테이너"""
    
    def setup_dependencies(self) -> None:
        """표준 의존성 설정"""
        from shared.core.redis_factory import RedisClientFactory
        
        # Redis 클라이언트 (싱글톤)
        self.registry.register_singleton(
            "redis_client", 
            lambda: RedisClientFactory.create_from_url()
        )
        
        logger.info("📦 표준 의존성 설정 완료") 