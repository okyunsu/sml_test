import redis
from typing import Optional
from urllib.parse import urlparse
import logging
import os

logger = logging.getLogger(__name__)

class RedisClientFactory:
    """공통 Redis 클라이언트 팩토리"""
    
    @staticmethod
    def create_from_url(
        redis_url: Optional[str] = None,
        default_host: str = "localhost",
        default_port: int = 6379,
        default_db: int = 0
    ) -> redis.Redis:
        """URL 또는 기본값으로 Redis 클라이언트 생성"""
        
        if not redis_url:
            redis_url = os.getenv("REDIS_URL", f"redis://{default_host}:{default_port}/{default_db}")
        
        try:
            parsed_url = urlparse(redis_url)
            
            client = redis.Redis(
                host=parsed_url.hostname or default_host,
                port=parsed_url.port or default_port,
                db=int(parsed_url.path[1:]) if parsed_url.path and parsed_url.path[1:] else default_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # 연결 테스트
            client.ping()
            logger.info(f"✅ Redis 연결 성공: {parsed_url.hostname}:{parsed_url.port}/{parsed_url.path[1:] if parsed_url.path else default_db}")
            
            return client
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis 연결 실패: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Redis 클라이언트 생성 오류: {str(e)}")
            raise
    
    @staticmethod
    def create_from_settings(
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ) -> redis.Redis:
        """개별 설정으로 Redis 클라이언트 생성"""
        
        try:
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # 연결 테스트
            client.ping()
            logger.info(f"✅ Redis 연결 성공: {host}:{port}/{db}")
            
            return client
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis 연결 실패: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Redis 클라이언트 생성 오류: {str(e)}")
            raise 