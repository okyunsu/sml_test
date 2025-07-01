#!/usr/bin/env python3
"""
뉴스 분석 전체 플로우 테스트 스크립트
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.domain.controller.news_controller import NewsController
from app.domain.model.news_dto import SimpleCompanySearchRequest
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_analysis_flow():
    """뉴스 분석 전체 플로우 테스트"""
    print("=== 뉴스 분석 플로우 테스트 시작 ===")
    
    try:
        # 1. 컨트롤러 초기화
        print("\n1. NewsController 초기화 중...")
        controller = NewsController()
        print("✅ NewsController 초기화 완료")
        
        # 2. 테스트 회사로 분석 요청
        test_company = "삼성전자"
        print(f"\n2. {test_company} 뉴스 분석 요청...")
        
        request = SimpleCompanySearchRequest(company=test_company)
        print(f"   - 검색 요청: {request}")
        
        # 3. 분석 실행
        print("\n3. 뉴스 분석 실행 중...")
        analysis_result = await controller.analyze_company_news(
            request.to_optimized_news_search_request()
        )
        
        print("✅ 뉴스 분석 완료!")
        
        # 4. 결과 요약 출력
        print("\n4. 분석 결과 요약:")
        print(f"   - 회사: {analysis_result.search_info['company']}")
        print(f"   - 총 뉴스 수: {analysis_result.search_info['total']}")
        print(f"   - 분석된 뉴스 수: {len(analysis_result.analyzed_news)}")
        print(f"   - ML 서비스 상태: {analysis_result.ml_service_status}")
        
        # 5. ESG 분포 확인
        if analysis_result.analysis_summary.esg_distribution:
            print(f"   - ESG 분포: {analysis_result.analysis_summary.esg_distribution}")
        
        # 6. 감정 분포 확인
        if analysis_result.analysis_summary.sentiment_distribution:
            print(f"   - 감정 분포: {analysis_result.analysis_summary.sentiment_distribution}")
        
        # 7. 샘플 뉴스 출력
        if analysis_result.analyzed_news:
            print(f"\n5. 샘플 분석 결과 (첫 3개):")
            for i, news in enumerate(analysis_result.analyzed_news[:3]):
                print(f"   [{i+1}] {news['title'][:50]}...")
                print(f"       ESG: {news.get('esg_classification', {}).get('category', 'N/A')}")
                print(f"       감정: {news.get('sentiment_analysis', {}).get('sentiment', 'N/A')}")
        
        print("\n✅ 뉴스 분석 플로우 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"\n❌ 뉴스 분석 플로우 테스트 실패: {str(e)}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}")
        return False

async def test_ml_service_availability():
    """ML 서비스 가용성 테스트"""
    print("\n=== ML 서비스 가용성 테스트 ===")
    
    try:
        from app.domain.service.ml_inference_service import MLInferenceService
        
        print("1. MLInferenceService 초기화 중...")
        ml_service = MLInferenceService()
        
        print(f"2. ML 서비스 상태: {'사용 가능' if ml_service.is_available() else '사용 불가'}")
        
        if ml_service.is_available():
            model_info = ml_service.get_model_info()
            print(f"3. 모델 정보: {model_info}")
            
            # 간단한 테스트
            test_text = "삼성전자가 새로운 기술을 발표했습니다."
            category_result = ml_service.predict_category(test_text)
            sentiment_result = ml_service.predict_sentiment(test_text)
            
            print(f"4. 테스트 분석 결과:")
            print(f"   - 카테고리: {category_result}")
            print(f"   - 감정: {sentiment_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML 서비스 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 뉴스 분석 시스템 종합 테스트 시작")
        
        # ML 서비스 테스트
        ml_ok = await test_ml_service_availability()
        
        # 전체 플로우 테스트
        flow_ok = await test_analysis_flow()
        
        print(f"\n📊 테스트 결과 요약:")
        print(f"   - ML 서비스: {'✅' if ml_ok else '❌'}")
        print(f"   - 분석 플로우: {'✅' if flow_ok else '❌'}")
        
        if ml_ok and flow_ok:
            print("\n🎉 모든 테스트 통과! 뉴스 분석 시스템이 정상 작동합니다.")
        else:
            print("\n⚠️ 일부 테스트 실패. 시스템 점검이 필요합니다.")
    
    asyncio.run(main()) 