#!/usr/bin/env python3
"""
Gateway API 테스트 스크립트
"""
import asyncio
import httpx
import json
from typing import Dict, Any

GATEWAY_URL = "http://localhost:8080"
NEWS_SERVICE_URL = "http://localhost:8002"


async def test_gateway_health():
    """Gateway 헬스 체크 테스트"""
    print("🏥 Gateway 헬스 체크 테스트...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{GATEWAY_URL}/gateway/v1/health")
            print(f"✅ 상태 코드: {response.status_code}")
            print(f"📄 응답: {response.json()}")
        except Exception as e:
            print(f"❌ 오류: {e}")


async def test_news_service_direct():
    """News Service 직접 연결 테스트"""
    print("\n🔍 News Service 직접 연결 테스트...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NEWS_SERVICE_URL}/health")
            print(f"✅ 상태 코드: {response.status_code}")
            print(f"📄 응답: {response.json()}")
        except Exception as e:
            print(f"❌ 오류: {e}")


async def test_news_search_via_gateway():
    """Gateway를 통한 뉴스 검색 테스트"""
    print("\n🔍 Gateway를 통한 뉴스 검색 테스트...")
    
    request_data = {
        "query": "삼성전자",
        "max_results": 5,
        "sort_by": "accuracy"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{GATEWAY_URL}/gateway/v1/news/search/news",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ 상태 코드: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"📄 검색 결과 수: {len(result.get('results', []))}")
                print(f"📄 응답 요약: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print(f"❌ 오류 응답: {response.text}")
        except Exception as e:
            print(f"❌ 오류: {e}")


async def test_company_search_via_gateway():
    """Gateway를 통한 회사 뉴스 검색 테스트"""
    print("\n🏢 Gateway를 통한 회사 뉴스 검색 테스트...")
    
    company = "삼성전자"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{GATEWAY_URL}/gateway/v1/news/search/companies/{company}",
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ 상태 코드: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"📄 검색 결과 수: {len(result.get('results', []))}")
                print(f"📄 응답 요약: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print(f"❌ 오류 응답: {response.text}")
        except Exception as e:
            print(f"❌ 오류: {e}")


async def test_dashboard_via_gateway():
    """Gateway를 통한 대시보드 API 테스트"""
    print("\n📊 Gateway를 통한 대시보드 API 테스트...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{GATEWAY_URL}/gateway/v1/news/dashboard/status")
            print(f"✅ 상태 코드: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"📄 대시보드 상태: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print(f"❌ 오류 응답: {response.text}")
        except Exception as e:
            print(f"❌ 오류: {e}")


async def main():
    """메인 테스트 함수"""
    print("🚀 Gateway API 테스트 시작\n")
    print("=" * 50)
    
    # 1. Gateway 헬스 체크
    await test_gateway_health()
    
    # 2. News Service 직접 연결 확인
    await test_news_service_direct()
    
    # 3. Gateway를 통한 뉴스 검색
    await test_news_search_via_gateway()
    
    # 4. Gateway를 통한 회사 뉴스 검색
    await test_company_search_via_gateway()
    
    # 5. Gateway를 통한 대시보드 API
    await test_dashboard_via_gateway()
    
    print("\n" + "=" * 50)
    print("🏁 테스트 완료")


if __name__ == "__main__":
    print("Gateway API 테스트 스크립트")
    print("사용 전 확인사항:")
    print("1. News Service가 http://localhost:8002 에서 실행 중인지 확인")
    print("2. Gateway가 http://localhost:8080 에서 실행 중인지 확인")
    print("")
    
    asyncio.run(main()) 