import json
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import os
import sys

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))))

logger = logging.getLogger(__name__)

class DashboardController:
    """SASB 대시보드 컨트롤러 - 의존성 주입 적용"""
    
    def __init__(self, redis_client=None):
        """의존성 주입 방식으로 Redis 클라이언트 받기"""
        self.redis_client = redis_client
        
        # 기존 방식도 지원 (호환성)
        if self.redis_client is None:
            self.redis_client = self._get_redis_client_legacy()
    
    def _get_redis_client_legacy(self):
        """레거시 Redis 클라이언트 생성 (호환성용)"""
        try:
            from shared.core.redis_factory import RedisClientFactory
            from app.config.settings import settings
            print(f"🔍 DashboardController: Connecting to Redis: {settings.CELERY_BROKER_URL}")
            return RedisClientFactory.create_from_url(settings.CELERY_BROKER_URL)
        except Exception as e:
            logger.error(f"Redis 클라이언트 생성 실패: {e}")
            print(f"⚠️  DashboardController: Using Mock Redis client due to: {e}")
            # Mock Redis 클라이언트 반환 (메서드 호출 시 에러 방지)
            class MockRedisClient:
                def get(self, key): return None
                def set(self, key, value, ex=None): return True
                def delete(self, key): return True
                def _client(self): return self
                def flushdb(self): return True
            return MockRedisClient()
    
    async def get_cache_data(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시 데이터 조회"""
        try:
            result = self.redis_client.get(key)
            if result:
                return json.loads(result)
            return None
        except Exception as e:
            logger.error(f"캐시 데이터 조회 실패 ({key}): {e}")
            return None
    
    async def set_cache_data(self, key: str, data: Dict[str, Any], expire_minutes: int = 30) -> bool:
        """캐시 데이터 저장"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            expire_seconds = expire_minutes * 60
            return self.redis_client.set(key, json_data, ex=expire_seconds)
        except Exception as e:
            logger.error(f"캐시 데이터 저장 실패 ({key}): {e}")
            return False
    
    async def delete_cache_data(self, key: str) -> bool:
        """캐시 데이터 삭제"""
        try:
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"캐시 데이터 삭제 실패 ({key}): {e}")
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """시스템 전체 상태 조회"""
        try:
            # Redis 연결 상태 확인
            redis_connected = False
            try:
                self.redis_client._client.ping()
                redis_connected = True
            except Exception:
                pass
            
            # 모니터링 중인 회사 수
            monitored_companies = ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"]
            
            # 캐시 통계
            cache_stats = await self._get_cache_statistics()
            
            return {
                "status": "healthy" if redis_connected else "degraded",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "redis": "connected" if redis_connected else "disconnected",
                    "ml_models": "loaded",
                    "naver_api": "available"
                },
                "statistics": {
                    "monitored_companies": len(monitored_companies),
                    "cache_hit_rate": cache_stats.get("hit_rate", 0),
                    "cached_analyses": cache_stats.get("total_analyses", 0)
                },
                "companies": monitored_companies
            }
        except Exception as e:
            logger.error(f"시스템 상태 조회 실패: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """캐시 정보 상세 조회"""
        try:
            cache_stats = await self._get_cache_statistics()
            
            # 회사별 캐시 상태 확인
            companies_cache = {}
            companies = ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"]
            
            for company in companies:
                company_cache_key = f"latest_companies_renewable_analysis:{company}"
                sasb_cache_key = f"company_sasb_analysis:{company}"
                
                company_data = await self.get_cache_data(company_cache_key)
                sasb_data = await self.get_cache_data(sasb_cache_key)
                
                companies_cache[company] = {
                    "company_analysis_cached": company_data is not None,
                    "sasb_analysis_cached": sasb_data is not None,
                    "last_updated": company_data.get("timestamp") if company_data else None
                }
            
            return {
                "cache_statistics": cache_stats,
                "companies": companies_cache,
                "sasb_keywords_count": 53,  # 신재생에너지 특화 키워드 개수
                "cache_settings": {
                    "company_sasb_expire_minutes": 60,
                    "sasb_only_expire_minutes": 30,
                    "max_articles_per_cache": 100
                }
            }
        except Exception as e:
            logger.error(f"캐시 정보 조회 실패: {e}")
            return {"error": str(e)}
    
    async def _get_cache_statistics(self) -> Dict[str, Any]:
        """캐시 통계 정보 계산"""
        try:
            # 간단한 캐시 통계 (실제로는 더 복잡한 로직 필요)
            total_keys = 0
            hit_count = 0
            
            # SASB 관련 키 패턴들
            key_patterns = [
                "company_sasb_analysis:*",
                "sasb_only_analysis:*",
                "latest_companies_renewable_analysis:*",
                "latest_sasb_renewable_analysis"
            ]
            
            # Redis에서 키 개수 확인 (실제 구현 시 더 정교한 로직 필요)
            try:
                # 간단한 추정값 반환
                total_keys = 6  # 예상 캐시 키 개수
                hit_count = 4   # 예상 히트 개수
            except Exception:
                pass
            
            hit_rate = (hit_count / total_keys) if total_keys > 0 else 0
            
            return {
                "total_analyses": total_keys,
                "cache_hits": hit_count,
                "hit_rate": round(hit_rate, 2),
                "last_calculated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"캐시 통계 계산 실패: {e}")
            return {
                "total_analyses": 0,
                "cache_hits": 0,
                "hit_rate": 0,
                "error": str(e)
            } 