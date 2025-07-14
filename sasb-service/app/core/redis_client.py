import redis
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, host: str, port: int, db: int):
        try:
            self._client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self._client.ping()
            logger.info("Successfully connected to Redis.")
        except redis.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            self._client = None

    def get(self, key: str) -> Optional[str]:
        if self._client:
            value = self._client.get(key)
            return str(value) if value is not None else None
        return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> Optional[bool]:
        if self._client:
            return bool(self._client.set(key, value, ex=ex))
        return None

    def delete(self, key: str) -> Any:
        """Deletes a key from Redis."""
        if self._client:
            return self._client.delete(key)
        return None 