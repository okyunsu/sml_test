from typing import Optional
from fastapi import HTTPException
import httpx
from app.domain.model.service_type import SERVICE_URLS, ServiceType

class ServiceProxyFactory:
    def __init__(self, service_type: ServiceType):
        self.base_url = SERVICE_URLS[service_type]
        self.service_type = service_type
        print(f"🔍 Service URL: {self.base_url}")
        
    async def request(
        self,
        method: str,
        path: str,
        headers: list[tuple[bytes, bytes]],
        body: Optional[bytes] = None
    ) -> httpx.Response:
        # ✅ news-service의 API 구조에 맞게 경로 매핑
        if self.service_type == ServiceType.NEWS:
            # news-service는 /api/v1/ 구조를 사용
            if not path.startswith("api/v1/"):
                # 기본 경로들을 news-service 구조에 매핑
                if path == "search":
                    path = "api/v1/search/news"
                elif path.startswith("companies/"):
                    # companies/{company} -> api/v1/search/companies/{company}
                    path = f"api/v1/search/{path}"
                elif path.startswith("dashboard"):
                    # dashboard 관련 요청
                    path = f"api/v1/{path}"
                elif path.startswith("system"):
                    # system 관련 요청
                    path = f"api/v1/{path}"
                else:
                    # 기타 경로들은 api/v1/search/ 하위로 매핑
                    if not path.startswith("api/"):
                        path = f"api/v1/search/{path}"
        
        url = f"{self.base_url}/{path}"
        print(f"🔍 Requesting URL: {url}")
        
        # 헤더 설정
        headers_dict = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers_dict,
                    content=body
                )
                print(f"Response status: {response.status_code}")
                print(f"Request URL: {url}")
                if body:
                    print(f"Request body: {body.decode('utf-8')}")
                return response
            except Exception as e:
                print(f"Request failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))