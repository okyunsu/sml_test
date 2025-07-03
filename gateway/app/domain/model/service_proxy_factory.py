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
        # ✅ news-service의 Gateway 호환 API로 단순 매핑
        if self.service_type == ServiceType.NEWS:
            # news-service에 추가된 Gateway 호환 엔드포인트로 직접 매핑
            # /api/v1/ 접두사를 추가하기만 하면 됨
            if not path.startswith("api/v1/"):
                path = f"api/v1/{path}"
        
        url = f"{self.base_url}/{path}"
        print(f"🔍 Requesting URL: {url}")
        print(f"🔍 Method: {method}")
        
        # 헤더 설정
        headers_dict = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # timeout 설정 추가 (30초)
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                print(f"🔍 Starting request to: {url}")
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers_dict,
                    content=body
                )
                print(f"✅ Response status: {response.status_code}")
                print(f"🔍 Response headers: {dict(response.headers)}")
                if body:
                    print(f"📤 Request body: {body.decode('utf-8')}")
                if response.text:
                    print(f"📥 Response body (first 500 chars): {response.text[:500]}")
                return response
                
            except httpx.TimeoutException as e:
                error_msg = f"Timeout error: {str(e)}"
                print(f"⏰ {error_msg}")
                raise HTTPException(status_code=504, detail=error_msg)
            except httpx.ConnectError as e:
                error_msg = f"Connection error: {str(e)}"
                print(f"🔌 {error_msg}")
                raise HTTPException(status_code=503, detail=error_msg)
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP status error: {e.response.status_code} - {e.response.text}"
                print(f"❌ {error_msg}")
                raise HTTPException(status_code=e.response.status_code, detail=error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)} (Type: {type(e).__name__})"
                print(f"💥 {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)