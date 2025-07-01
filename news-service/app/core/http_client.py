"""HTTP 클라이언트 설정 및 관리"""
import httpx
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class HttpClientConfig:
    """HTTP 클라이언트 설정"""
    max_keepalive_connections: int = 20
    max_connections: int = 100
    keepalive_expiry: float = 30.0
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    write_timeout: float = 10.0
    pool_timeout: float = 5.0
    user_agent: str = "News-Service/1.0"

class HttpClientManager:
    """HTTP 클라이언트 관리자"""
    
    def __init__(self, config: Optional[HttpClientConfig] = None):
        self.config = config or HttpClientConfig()
        self._limits = httpx.Limits(
            max_keepalive_connections=self.config.max_keepalive_connections,
            max_connections=self.config.max_connections,
            keepalive_expiry=self.config.keepalive_expiry
        )
        self._timeout = httpx.Timeout(
            connect=self.config.connect_timeout,
            read=self.config.read_timeout,
            write=self.config.write_timeout,
            pool=self.config.pool_timeout
        )
    
    @asynccontextmanager
    async def get_client(self, headers: Optional[Dict[str, str]] = None):
        """비동기 HTTP 클라이언트 컨텍스트 매니저"""
        default_headers = {"User-Agent": self.config.user_agent}
        if headers:
            default_headers.update(headers)
            
        async with httpx.AsyncClient(
            limits=self._limits,
            timeout=self._timeout,
            headers=default_headers
        ) as client:
            yield client

# ML 서비스용 특별 설정
@dataclass 
class MLHttpClientConfig(HttpClientConfig):
    """ML 서비스용 HTTP 클라이언트 설정"""
    max_keepalive_connections: int = 10
    max_connections: int = 50
    read_timeout: float = 120.0
    user_agent: str = "News-Analysis-Service/1.0" 