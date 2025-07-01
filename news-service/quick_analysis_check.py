#!/usr/bin/env python3
"""
분석 결과 빠른 확인 스크립트
"""
import requests
import json
from datetime import datetime

def check_analysis_status():
    """분석 상태 확인"""
    print("=== 뉴스 분석 상태 확인 ===")
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    companies = ["삼성전자", "LG전자"]
    
    for company in companies:
        try:
            print(f"\n📊 {company} 분석 결과:")
            
            # API 호출
            response = requests.get(f'http://localhost:8002/api/v1/dashboard/analysis/{company}')
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success' and result.get('data'):
                    data = result['data']
                    analysis = data.get('analysis_result', {})
                    
                    print(f"   ✅ 상태: 분석 완료")
                    print(f"   📅 분석 시간: {data.get('analyzed_at', 'N/A')}")
                    print(f"   📰 분석된 뉴스: {len(analysis.get('analyzed_news', []))}개")
                    
                    # 분석 요약
                    summary = analysis.get('analysis_summary', {})
                    if summary:
                        print(f"   🎯 총 분석: {summary.get('total_analyzed', 0)}개")
                        esg_dist = summary.get('esg_distribution', {})
                        if esg_dist:
                            print(f"   📈 ESG 분포: {esg_dist}")
                        sentiment_dist = summary.get('sentiment_distribution', {})
                        if sentiment_dist:
                            print(f"   😊 감정 분포: {sentiment_dist}")
                    
                    # 첫 번째 뉴스 샘플
                    analyzed_news = analysis.get('analyzed_news', [])
                    if analyzed_news:
                        first_news = analyzed_news[0]
                        print(f"   📰 샘플 뉴스: {first_news.get('title', 'N/A')[:50]}...")
                        print(f"      ESG: {first_news.get('esg_classification', {}).get('category', 'N/A')}")
                        print(f"      감정: {first_news.get('sentiment_analysis', {}).get('sentiment', 'N/A')}")
                        
                else:
                    print(f"   ⏳ 상태: 분석 진행 중 또는 대기 중")
                    print(f"   📝 메시지: {result.get('message', 'N/A')}")
                    
            else:
                print(f"   ❌ API 호출 실패 (상태 코드: {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ 오류 발생: {str(e)}")
    
    # 전체 상태 확인
    try:
        print(f"\n🔍 전체 시스템 상태:")
        response = requests.get('http://localhost:8002/api/v1/dashboard/status')
        if response.status_code == 200:
            status = response.json()
            print(f"   Redis 연결: {status.get('redis_connected', False)}")
            print(f"   모니터링 회사: {status.get('monitored_companies', [])}")
            print(f"   마지막 분석: {status.get('last_analysis_time', 'N/A')}")
        else:
            print(f"   ❌ 상태 확인 실패")
    except Exception as e:
        print(f"   ❌ 상태 확인 오류: {str(e)}")

if __name__ == "__main__":
    check_analysis_status() 