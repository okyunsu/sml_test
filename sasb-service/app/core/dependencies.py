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
            # Mock ML 서비스 생성 (키워드 기반 감성분석)
            class MockMLInferenceService:
                def __init__(self):
                    self.tokenizer = None
                    self.model = None
                    self.device = None
                    print("✅ Mock ML Inference Service (키워드 기반 감성분석) 초기화 완료")
                    
                    # ESG/SASB 특화 긍정 키워드
                    self.positive_keywords = [
                        # 성과/개선
                        "성과", "개선", "향상", "증가", "상승", "성장", "발전", "진전", "혁신", "성공",
                        "달성", "완료", "구축", "강화", "확대", "확충", "도입", "시행", "추진", "실현",
                        
                        # 친환경/지속가능성
                        "친환경", "지속가능", "그린", "청정", "신재생", "재생에너지", "탄소중립", "저탄소",
                        "에너지효율", "절약", "절감", "저감", "순환경제", "재활용", "재사용",
                        
                        # 안전/품질
                        "안전", "안전성", "품질", "신뢰", "투명", "윤리", "준수", "컴플라이언스",
                        "인증", "수상", "선정", "우수", "최고", "최우수", "1위", "선도",
                        
                        # 협력/상생
                        "협력", "상생", "파트너십", "동반성장", "지원", "투자", "기여", "참여",
                        "소통", "공유", "나눔", "기부", "봉사", "사회공헌"
                    ]
                    
                    # ESG/SASB 특화 부정 키워드
                    self.negative_keywords = [
                        # 사고/문제
                        "사고", "사망", "부상", "화재", "폭발", "누출", "오염", "피해", "손실", "손상",
                        "고장", "결함", "불량", "오류", "실패", "중단", "정지", "차질", "지연", "취소",
                        
                        # 위반/처벌
                        "위반", "위법", "불법", "처벌", "제재", "과태료", "벌금", "과징금", "고발", "고소",
                        "조사", "감사", "적발", "적발", "단속", "검찰", "수사", "기소",
                        
                        # 환경 악화
                        "오염", "배출", "누출", "유출", "방출", "폐기", "훼손", "파괴", "악화", "저하",
                        "초과", "부족", "미달", "미흡", "불충분", "불만족", "불합격",
                        
                        # 경영 악화
                        "적자", "손실", "감소", "하락", "악화", "부실", "파산", "도산", "부도", "위기",
                        "논란", "갈등", "분쟁", "반대", "항의", "규탄", "비판", "문제", "우려", "불안"
                    ]
                    
                def analyze_sentiment(self, text: str, description: str = None) -> dict:
                    """개선된 키워드 기반 감성 분석"""
                    if not text or not isinstance(text, str) or not text.strip():
                        return {"sentiment": "중립", "confidence": 0.0, "matched_positive_keywords": [], "matched_negative_keywords": []}
                    
                    # 제목 + 설명 결합 분석
                    full_text = text
                    if description and isinstance(description, str) and description.strip():
                        full_text = f"{text} {description}"
                    
                    # 한글 텍스트는 lower() 대신 strip()만 사용
                    full_text = full_text.strip()
                    
                    # 키워드 매칭 (정확한 매칭을 위해 공백으로 분리된 단어 단위로 검사)
                    matched_positive = []
                    matched_negative = []
                    
                    for keyword in self.positive_keywords:
                        if keyword in full_text:
                            matched_positive.append(keyword)
                    
                    for keyword in self.negative_keywords:
                        if keyword in full_text:
                            matched_negative.append(keyword)
                    
                    positive_count = len(matched_positive)
                    negative_count = len(matched_negative)
                    
                    # 개선된 감성 판단 로직
                    if positive_count > negative_count:
                        sentiment = "긍정"
                        # confidence: 0.6 ~ 0.95 (키워드 개수와 차이에 비례)
                        confidence = min(0.6 + (positive_count - negative_count) * 0.1, 0.95)
                    elif negative_count > positive_count:
                        sentiment = "부정"
                        # confidence: 0.6 ~ 0.95 (키워드 개수와 차이에 비례)
                        confidence = min(0.6 + (negative_count - positive_count) * 0.1, 0.95)
                    elif positive_count > 0 or negative_count > 0:
                        sentiment = "중립"
                        confidence = 0.4  # 키워드가 있지만 동점인 경우
                    else:
                        sentiment = "중립"
                        confidence = 0.0  # 키워드가 전혀 없는 경우
                    
                    return {
                        "sentiment": sentiment, 
                        "confidence": confidence,
                        "matched_positive_keywords": matched_positive[:5],  # 상위 5개만
                        "matched_negative_keywords": matched_negative[:5],   # 상위 5개만
                        "analysis_method": "keyword_based",
                        "total_positive_matches": positive_count,
                        "total_negative_matches": negative_count
                    }
            
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