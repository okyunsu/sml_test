#!/usr/bin/env python3
"""
Dashboard 기능 테스트 스크립트

이 스크립트는 Redis + Celery 기반 대시보드 API를 테스트합니다.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8002"
DASHBOARD_BASE = f"{BASE_URL}/api/v1/dashboard"
COMPANIES = ["삼성전자", "LG전자"]


async def test_dashboard_apis():
    """대시보드 API 테스트"""
    
    print("🚀 News Service Dashboard API 테스트 시작\n")
    
    async with httpx.AsyncClient() as client:
        
        # 1. 서비스 헬스체크
        print("1️⃣ 서비스 헬스체크")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ News Service 실행 중")
            else:
                print("❌ News Service 연결 실패")
                return
        except Exception as e:
            print(f"❌ 서비스 연결 실패: {e}")
            return
        
        print()
        
        # 2. 대시보드 상태 확인
        print("2️⃣ 대시보드 상태 확인")
        try:
            response = await client.get(f"{DASHBOARD_BASE}/status")
            status_data = response.json()
            
            print(f"   상태: {status_data.get('status', 'unknown')}")
            print(f"   Redis 연결: {status_data.get('redis_connected', False)}")
            print(f"   모니터링 회사: {status_data.get('monitored_companies', [])}")
            print(f"   마지막 분석: {status_data.get('last_analysis_at', 'N/A')}")
            
            if not status_data.get('redis_connected', False):
                print("⚠️  Redis가 연결되지 않았습니다. docker-compose.redis.yml로 실행하세요.")
                
        except Exception as e:
            print(f"❌ 상태 확인 실패: {e}")
        
        print()
        
        # 3. 모니터링 회사 목록 확인
        print("3️⃣ 모니터링 회사 목록")
        try:
            response = await client.get(f"{DASHBOARD_BASE}/companies")
            companies_data = response.json()
            
            print(f"   등록된 회사: {companies_data.get('companies', [])}")
            print(f"   총 회사 수: {companies_data.get('total_count', 0)}")
            print(f"   분석 주기: {companies_data.get('analysis_interval', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 회사 목록 조회 실패: {e}")
        
        print()
        
        # 4. 캐시 정보 확인
        print("4️⃣ 캐시 정보 확인")
        try:
            response = await client.get(f"{DASHBOARD_BASE}/cache/info")
            cache_data = response.json()
            
            print(f"   총 캐시 키 수: {cache_data.get('total_cache_keys', 0)}")
            
            for company, info in cache_data.get('companies', {}).items():
                print(f"   {company}:")
                print(f"     - 최신 분석 캐시: {info.get('latest_cached', False)}")
                print(f"     - 히스토리 개수: {info.get('history_count', 0)}")
                
        except Exception as e:
            print(f"❌ 캐시 정보 조회 실패: {e}")
        
        print()
        
        # 5. 수동 분석 테스트 (삼성전자)
        print("5️⃣ 수동 분석 테스트 (삼성전자)")
        try:
            print("   분석 요청 중...")
            response = await client.post(f"{DASHBOARD_BASE}/analyze/삼성전자")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 분석 요청 성공")
                print(f"   작업 ID: {result.get('task_id', 'N/A')}")
                print(f"   요청 시간: {result.get('requested_at', 'N/A')}")
                print("   ⏳ 백그라운드에서 분석 진행 중... (1-2분 소요)")
            else:
                print(f"❌ 분석 요청 실패: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 수동 분석 실패: {e}")
        
        print()
        
        # 6. 분석 결과 대기 및 확인
        print("6️⃣ 분석 결과 확인 (30초 후)")
        time.sleep(30)
        
        for company in COMPANIES:
            try:
                response = await client.get(f"{DASHBOARD_BASE}/analysis/{company}")
                analysis_data = response.json()
                
                print(f"   {company}:")
                print(f"     상태: {analysis_data.get('status', 'N/A')}")
                print(f"     분석 시간: {analysis_data.get('analyzed_at', 'N/A')}")
                
                if analysis_data.get('status') == 'success':
                    result = analysis_data.get('analysis_result', {})
                    news_count = len(result.get('analyzed_news', []))
                    print(f"     분석된 뉴스 수: {news_count}")
                    
                    if news_count > 0:
                        print("     ESG 분포:")
                        summary = result.get('analysis_summary', {})
                        esg_dist = summary.get('esg_distribution', {})
                        for category, count in esg_dist.items():
                            print(f"       {category}: {count}개")
                
            except Exception as e:
                print(f"   ❌ {company} 분석 결과 조회 실패: {e}")
        
        print()
        
        # 7. 전체 최신 분석 결과 확인
        print("7️⃣ 전체 최신 분석 결과")
        try:
            response = await client.get(f"{DASHBOARD_BASE}/latest")
            latest_data = response.json()
            
            print(f"   조회 시간: {latest_data.get('retrieved_at', 'N/A')}")
            
            for company, result in latest_data.get('results', {}).items():
                print(f"   {company}: {result.get('status', 'N/A')}")
                if result.get('analyzed_at'):
                    print(f"     분석 시간: {result['analyzed_at']}")
                    
        except Exception as e:
            print(f"❌ 전체 분석 결과 조회 실패: {e}")
        
        print()
        
    print("🎉 테스트 완료!")
    print("\n📋 다음 단계:")
    print("1. Swagger UI 확인: http://localhost:8002/docs")
    print("2. 30분 후 자동 분석 결과 확인")
    print("3. 프론트엔드에서 API 연동")


def test_redis_connection():
    """Redis 연결 테스트"""
    print("🔍 Redis 연결 테스트")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("✅ Redis 연결 성공")
        
        # 테스트 데이터 저장/조회
        test_key = "dashboard:test"
        test_data = {"test": True, "timestamp": datetime.now().isoformat()}
        
        r.set(test_key, json.dumps(test_data))
        retrieved_data = r.get(test_key)
        if retrieved_data:
            retrieved = json.loads(retrieved_data)
            if retrieved.get("test"):
                print("✅ Redis 읽기/쓰기 정상")
        else:
            print("❌ Redis 데이터 조회 실패")
        
        r.delete(test_key)
        print("✅ Redis 테스트 완료")
        
    except ImportError:
        print("❌ Redis 패키지가 설치되지 않았습니다: pip install redis")
    except Exception as e:
        print(f"❌ Redis 연결 실패: {e}")
        print("   Redis 서버가 실행 중인지 확인하세요:")
        print("   docker run -d --name redis -p 6379:6379 redis:7-alpine")


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 News Service Dashboard 테스트")
    print("=" * 60)
    print()
    
    # Redis 연결 테스트
    test_redis_connection()
    print()
    
    # API 테스트 실행
    asyncio.run(test_dashboard_apis()) 