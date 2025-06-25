#!/usr/bin/env python3
"""
간소화된 뉴스 API 테스트 스크립트

사용법:
    python test_simple_api.py

테스트하는 엔드포인트:
1. POST /api/v1/news/company/simple - 간소화된 회사 뉴스 검색
2. POST /api/v1/news/company/simple/analyze - 간소화된 회사 뉴스 분석
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# API 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1/news"

async def test_simple_company_search():
    """간소화된 회사 뉴스 검색 테스트"""
    print("=" * 60)
    print("📰 간소화된 회사 뉴스 검색 테스트")
    print("=" * 60)
    
    # 테스트할 회사 목록
    companies = ["삼성전자", "LG전자", "SK하이닉스", "현대자동차"]
    
    async with aiohttp.ClientSession() as session:
        for company in companies:
            print(f"\n🏢 회사: {company}")
            print("-" * 40)
            
            # 요청 데이터 (회사명만 필요!)
            request_data = {
                "company": company
            }
            
            try:
                # API 호출
                async with session.post(
                    f"{BASE_URL}{API_PREFIX}/company/simple",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        print(f"✅ 검색 성공!")
                        print(f"📊 총 뉴스 수: {data['total']}")
                        print(f"📋 반환된 뉴스 수: {len(data['items'])}")
                        print(f"🔄 중복 제거됨: {data.get('duplicates_removed', 0)}개")
                        
                        # 상위 3개 뉴스 제목 출력
                        if data['items']:
                            print(f"\n📑 상위 뉴스 제목:")
                            for i, item in enumerate(data['items'][:3], 1):
                                title = item['title'][:50] + "..." if len(item['title']) > 50 else item['title']
                                print(f"  {i}. {title}")
                    else:
                        print(f"❌ 검색 실패: {response.status}")
                        error_text = await response.text()
                        print(f"   오류 내용: {error_text}")
                        
            except Exception as e:
                print(f"❌ 요청 오류: {str(e)}")

async def test_simple_company_analysis():
    """간소화된 회사 뉴스 분석 테스트"""
    print("\n" + "=" * 60)
    print("🔍 간소화된 회사 뉴스 분석 테스트")
    print("=" * 60)
    
    # 테스트할 회사 (분석은 시간이 오래 걸리므로 1개만)
    company = "삼성전자"
    
    async with aiohttp.ClientSession() as session:
        print(f"\n🏢 회사: {company}")
        print("-" * 40)
        
        # 요청 데이터 (회사명만 필요!)
        request_data = {
            "company": company
        }
        
        try:
            print("🔄 뉴스 검색 및 분석 중... (시간이 걸릴 수 있습니다)")
            
            # API 호출 (타임아웃 60초)
            timeout = aiohttp.ClientTimeout(total=60)
            async with session.post(
                f"{BASE_URL}{API_PREFIX}/company/simple/analyze",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"✅ 분석 성공!")
                    
                    # 검색 정보
                    search_info = data.get('search_info', {})
                    print(f"📊 검색된 뉴스 수: {search_info.get('total', 0)}")
                    
                    # 분석 요약
                    summary = data.get('analysis_summary', {})
                    print(f"🔍 분석된 뉴스 수: {summary.get('total_analyzed', 0)}")
                    
                    # ESG 분포
                    esg_dist = summary.get('esg_distribution', {})
                    if esg_dist:
                        print(f"\n📈 ESG 카테고리 분포:")
                        for category, count in esg_dist.items():
                            print(f"  • {category}: {count}건")
                    
                    # 감정 분포
                    sentiment_dist = summary.get('sentiment_distribution', {})
                    if sentiment_dist:
                        print(f"\n😊 감정 분석 결과:")
                        for sentiment, count in sentiment_dist.items():
                            emoji = {"긍정": "😊", "부정": "😞", "중립": "😐"}.get(sentiment, "📊")
                            print(f"  {emoji} {sentiment}: {count}건")
                    
                    # ML 서비스 상태
                    ml_status = data.get('ml_service_status', 'unknown')
                    status_emoji = "🤖" if ml_status == "success" else "⚠️"
                    print(f"\n{status_emoji} ML 서비스 상태: {ml_status}")
                    
                else:
                    print(f"❌ 분석 실패: {response.status}")
                    error_text = await response.text()
                    print(f"   오류 내용: {error_text}")
                    
        except asyncio.TimeoutError:
            print("⏰ 분석 요청이 시간 초과되었습니다")
        except Exception as e:
            print(f"❌ 요청 오류: {str(e)}")

async def test_health_check():
    """헬스체크 테스트"""
    print("\n" + "=" * 60)
    print("🏥 서비스 헬스체크")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}{API_PREFIX}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 서비스 상태: {data.get('status', 'unknown')}")
                    print(f"🔧 서비스명: {data.get('service', 'unknown')}")
                    print(f"📦 버전: {data.get('version', 'unknown')}")
                    print(f"⚡ 비동기 최적화: {data.get('async_optimized', False)}")
                else:
                    print(f"❌ 헬스체크 실패: {response.status}")
        except Exception as e:
            print(f"❌ 헬스체크 오류: {str(e)}")

def print_usage_examples():
    """사용 예시 출력"""
    print("\n" + "=" * 60)
    print("📖 API 사용 예시")
    print("=" * 60)
    
    print("\n🔹 간소화된 회사 뉴스 검색:")
    print("POST /api/v1/news/company/simple")
    print("Content-Type: application/json")
    print(json.dumps({"company": "삼성전자"}, indent=2, ensure_ascii=False))
    
    print("\n🔹 간소화된 회사 뉴스 분석:")
    print("POST /api/v1/news/company/simple/analyze")
    print("Content-Type: application/json")
    print(json.dumps({"company": "삼성전자"}, indent=2, ensure_ascii=False))
    
    print("\n🔹 최적화된 고정 설정:")
    print("  • 검색 결과: 100개")
    print("  • 정렬: 정확도 순 (관련성 높은 뉴스 우선)")
    print("  • 검색 시작 위치: 1 (가장 관련성 높은 뉴스부터)")
    print("  • 중복 제거: 활성화")
    print("  • 유사도 임계값: 0.75")

async def main():
    """메인 테스트 실행"""
    print("🚀 간소화된 뉴스 API 테스트 시작")
    print(f"📍 서버 URL: {BASE_URL}")
    
    # 사용 예시 출력
    print_usage_examples()
    
    # 헬스체크
    await test_health_check()
    
    # 간소화된 검색 테스트
    await test_simple_company_search()
    
    # 간소화된 분석 테스트 (시간이 오래 걸림)
    print(f"\n⚠️  분석 테스트는 시간이 오래 걸릴 수 있습니다.")
    user_input = input("분석 테스트를 실행하시겠습니까? (y/N): ")
    
    if user_input.lower() in ['y', 'yes']:
        await test_simple_company_analysis()
    else:
        print("분석 테스트를 건너뛰었습니다.")
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    print("간소화된 뉴스 API 테스트")
    print("주의: 뉴스 서비스가 http://localhost:8000 에서 실행 중이어야 합니다.")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 테스트를 중단했습니다.")
    except Exception as e:
        print(f"\n\n❌ 테스트 실행 중 오류 발생: {str(e)}") 