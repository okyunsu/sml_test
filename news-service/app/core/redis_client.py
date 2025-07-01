import json
import redis
import os
from typing import Any, Dict, Optional
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 클라이언트 - 뉴스 분석 결과 캐싱용"""
    
    def __init__(self):
        # 환경변수 또는 설정에서 Redis 연결 정보 가져오기
        self.host = settings.redis_host
        self.port = settings.redis_port
        self.db = settings.redis_db
        self.client = None
        
    def connect(self):
        """Redis 연결"""
        try:
            logger.info(f"Redis 연결 시도: host={self.host}, port={self.port}, db={self.db}")
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            # 연결 테스트
            self.client.ping()
            logger.info(f"Redis 연결 성공: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Redis 연결 실패 ({self.host}:{self.port}): {str(e)}")
            raise
    
    def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """JSON 데이터 저장"""
        try:
            if not self.client:
                self.connect()
                
            json_data = json.dumps(value, ensure_ascii=False, default=str)
            
            if expire:
                return self.client.setex(key, expire, json_data)
            else:
                return self.client.set(key, json_data)
        except Exception as e:
            logger.error(f"Redis set_json 오류: {str(e)}")
            return False
    
    def get_json(self, key: str) -> Optional[Any]:
        """JSON 데이터 조회"""
        try:
            if not self.client:
                self.connect()
                
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get_json 오류: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """키 삭제"""
        try:
            if not self.client:
                self.connect()
                
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete 오류: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """키 존재 확인"""
        try:
            if not self.client:
                self.connect()
                
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists 오류: {str(e)}")
            return False
    
    def get_all_keys(self, pattern: str = "*") -> list:
        """패턴 매칭으로 모든 키 조회"""
        try:
            if not self.client:
                self.connect()
                
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis get_all_keys 오류: {str(e)}")
            return []


# 전역 Redis 클라이언트 인스턴스
redis_client = RedisClient() 