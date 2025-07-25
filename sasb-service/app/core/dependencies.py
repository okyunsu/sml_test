from typing import Dict, Any
import os
import sys

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

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
        try:
            print(f"🔍 DEBUG: Trying to connect to Redis: {settings.CELERY_BROKER_URL}")
            redis_client = RedisClientFactory.create_from_url(settings.CELERY_BROKER_URL)
            print("✅ Redis connection successful")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            print("⚠️  Using mock Redis client for development")
            redis_client = None  # 임시로 None 처리
        
        # 2. 기본 서비스 계층 (의존성 없음)
        naver_news_service = NaverNewsService()
        
        # ML 모델 서비스 - 환경변수에 따라 조건부 생성
        disable_ml = os.getenv("DISABLE_ML_MODEL", "false").lower() == "true"
        if disable_ml:
            print("🔧 ML 모델이 비활성화되었습니다. Mock ML 서비스를 사용합니다.")
            # Mock ML 서비스 생성 (모델 없이 기본값 반환)
            class MockMLInferenceService:
                def __init__(self):
                    self.tokenizer = None
                    self.model = None
                    self.device = None
                    print("✅ Mock ML Inference Service 초기화 완료")
                
                def analyze_sentiment(self, text: str) -> dict:
                    """Mock 감성 분석 - 항상 중립 반환"""
                    return {"sentiment": "중립", "confidence": 0.0}
            
            ml_inference_service = MockMLInferenceService()
        else:
            print("🤖 ML 모델이 활성화되었습니다. 실제 ML 서비스를 로딩합니다.")
            ml_inference_service = MLInferenceService()
        
        # 3. 중간 서비스 계층 (기본 서비스들에 의존)
        analysis_service = AnalysisService()
        
        # 4. 고수준 서비스 계층 (다른 서비스들에 의존)
        sasb_service = SASBService()
        
        # 5. 컨트롤러 계층 (서비스들에 의존)
        sasb_controller = SASBController()
        
        # DashboardController 초기화 (Redis 연결 실패 시에도 앱 시작 가능하게 함)
        try:
            dashboard_controller = DashboardController()
            print("✅ DashboardController initialized successfully")
        except Exception as e:
            print(f"❌ DashboardController initialization failed: {e}")
            print("⚠️  Creating mock DashboardController")
            # Mock DashboardController 사용
            class MockDashboardController:
                async def get_cache_data(self, key): return None
                async def set_cache_data(self, key, data, ttl=3600): return True
                async def delete_cache_data(self, key): return True
                async def get_cache_stats(self): return {"error": "Redis unavailable"}
            dashboard_controller = MockDashboardController()
        
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