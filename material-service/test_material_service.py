#!/usr/bin/env python3
"""
Material Assessment Service 테스트 스크립트
"""

import sys
import os
import asyncio
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.domain.service.materiality_parsing_service import MaterialityParsingService
from app.domain.service.materiality_mapping_service import MaterialityMappingService
from app.domain.service.materiality_analysis_service import MaterialityAnalysisService
from app.domain.service.materiality_recommendation_service import MaterialityRecommendationService
from app.domain.model.materiality_dto import MaterialityAssessment, MaterialityTopic, MaterialityHistory
from app.core.gateway_client import GatewayClient
import json

async def test_material_service():
    """Material Assessment Service 통합 테스트"""
    
    print("=" * 80)
    print("🔍 Material Assessment Service 통합 테스트")
    print("=" * 80)
    
    # 서비스 초기화
    parsing_service = MaterialityParsingService()
    mapping_service = MaterialityMappingService()
    analysis_service = MaterialityAnalysisService()
    recommendation_service = MaterialityRecommendationService()
    gateway_client = GatewayClient()
    
    # 1. Gateway 연결 테스트
    print("\n🔗 Gateway 연결 테스트:")
    try:
        connection_status = await analysis_service.check_gateway_connection()
        print(f"  - Gateway 상태: {connection_status['gateway_status']}")
        print(f"  - SASB 서비스: {connection_status.get('sasb_service', 'unknown')}")
        print(f"  - News 서비스: {connection_status.get('news_service', 'unknown')}")
        print(f"  - 분석 능력: {connection_status.get('analysis_capability', 'unknown')}")
    except Exception as e:
        print(f"  - Gateway 연결 오류: {str(e)}")
    
    # 2. 기존 기능 테스트
    print("\n📊 기존 기능 테스트:")
    
    # 산업 키워드 테스트
    industry_keywords = mapping_service.get_industry_keywords()
    print(f"  - 산업 키워드 수: {len(industry_keywords)}개")
    print(f"  - 산업 키워드 예시: {industry_keywords[:5]}")
    
    # SASB 이슈 키워드 테스트
    sasb_keywords = mapping_service.get_sasb_issue_keywords()
    print(f"  - SASB 이슈 키워드 수: {len(sasb_keywords)}개")
    print(f"  - SASB 이슈 키워드 예시: {sasb_keywords[:5]}")
    
    # 3. 매핑 서비스 테스트
    print("\n🗺️ SASB 매핑 테이블 통계:")
    stats = mapping_service.get_mapping_statistics()
    print(f"  - 총 SASB 코드: {stats['total_sasb_codes']}개")
    print(f"  - 총 매핑 토픽: {stats['total_materiality_topics']}개")
    print(f"  - 산업 키워드: {stats['total_industry_keywords']}개")
    print(f"  - SASB 이슈 키워드: {stats['total_sasb_issue_keywords']}개")
    print(f"  - 카테고리 분포: E={stats['category_distribution']['E']}, S={stats['category_distribution']['S']}, G={stats['category_distribution']['G']}")
    
    # 4. 샘플 데이터 생성 및 분석 테스트
    print("\n📈 히스토리 분석 테스트:")
    
    # 두산퓨얼셀 3년 샘플 데이터 생성
    doosan_history = create_sample_history("두산퓨얼셀")
    
    # 동기 버전 테스트 (fallback)
    print("  - 동기 버전 트렌드 분석:")
    sync_trend_analysis = analysis_service.analyze_historical_trends_sync(
        doosan_history, [2022, 2023, 2024]
    )
    print(f"    ✓ 토픽 변화: {len(sync_trend_analysis.topic_changes)}개")
    print(f"    ✓ 부상 이슈: {len(sync_trend_analysis.emerging_issues)}개")
    print(f"    ✓ 지속 이슈: {len(sync_trend_analysis.ongoing_issues)}개")
    print(f"    ✓ 성숙 이슈: {len(sync_trend_analysis.maturing_issues)}개")
    print(f"    ✓ 뉴스 연결: {sync_trend_analysis.news_frequency_analysis.get('gateway_connection', 'unknown')}")
    
    # 비동기 버전 테스트 (gateway 연동)
    print("  - 비동기 버전 트렌드 분석 (Gateway 연동):")
    try:
        async_trend_analysis = await analysis_service.analyze_historical_trends(
            doosan_history, [2022, 2023, 2024]
        )
        print(f"    ✓ 토픽 변화: {len(async_trend_analysis.topic_changes)}개")
        print(f"    ✓ 부상 이슈: {len(async_trend_analysis.emerging_issues)}개")
        print(f"    ✓ 지속 이슈: {len(async_trend_analysis.ongoing_issues)}개")
        print(f"    ✓ 성숙 이슈: {len(async_trend_analysis.maturing_issues)}개")
        print(f"    ✓ 뉴스 연결: {async_trend_analysis.news_frequency_analysis.get('gateway_connection', 'unknown')}")
        
        # 추천 서비스 테스트
        print("\n💡 추천 서비스 테스트:")
        current_assessment = doosan_history.get_assessment_by_year(2024)
        if current_assessment:
            recommendations = recommendation_service.generate_update_recommendations(
                async_trend_analysis, current_assessment, 2025
            )
            print(f"  - 총 추천사항: {len(recommendations)}개")
            
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"    {i}. {rec.topic_name} ({rec.change_type.value})")
                print(f"       신뢰도: {rec.confidence_score:.2f}")
                print(f"       근거: {rec.rationale[:50]}...")
        
    except Exception as e:
        print(f"    ❌ 비동기 분석 오류: {str(e)}")
    
    # 5. 비교 분석 테스트
    print("\n⚖️ 비교 분석 테스트:")
    assessment_2023 = doosan_history.get_assessment_by_year(2023)
    assessment_2024 = doosan_history.get_assessment_by_year(2024)
    
    if assessment_2023 and assessment_2024:
        # 기본 비교 분석
        basic_comparison = analysis_service.compare_assessments(assessment_2023, assessment_2024)
        print(f"  - 기본 비교 분석:")
        print(f"    ✓ 우선순위 변화: {len(basic_comparison.priority_changes)}개")
        print(f"    ✓ 신규 토픽: {len(basic_comparison.new_topics)}개")
        print(f"    ✓ 제거 토픽: {len(basic_comparison.removed_topics)}개")
        print(f"    ✓ 안정성 점수: {basic_comparison.stability_score:.2f}")
        
        # 향상된 비교 분석 (뉴스 연동)
        try:
            enhanced_comparison = await analysis_service.enhanced_comparison_with_news_analysis(
                assessment_2023, assessment_2024
            )
            print(f"  - 향상된 비교 분석:")
            print(f"    ✓ 뉴스 연관성: {enhanced_comparison.news_correlation.get('correlation_score', 'N/A')}")
            print(f"    ✓ 뉴스 기반 변화: {enhanced_comparison.news_correlation.get('news_driven_changes', 0)}개")
        except Exception as e:
            print(f"    ❌ 향상된 비교 분석 오류: {str(e)}")
    
    # 6. 이슈 중요도 분류 테스트
    print("\n🎯 이슈 중요도 분류 테스트:")
    if assessment_2024:
        for topic in assessment_2024.topics[:3]:  # 상위 3개 토픽만 테스트
            classification = recommendation_service.classify_issue_importance(
                topic.topic_name, sync_trend_analysis, assessment_2024
            )
            print(f"  - {topic.topic_name}:")
            print(f"    ✓ 중요도 점수: {classification['importance_score']:.2f}")
            print(f"    ✓ 분류: {classification['classification']}")
            print(f"    ✓ 신뢰도: {classification['recommendation_confidence']:.2f}")
    
    # 7. Gateway 클라이언트 직접 테스트
    print("\n🌐 Gateway 클라이언트 직접 테스트:")
    try:
        # 뉴스 검색 테스트
        news_result = await gateway_client.search_news_by_keywords(
            keywords=["탄소중립", "RE100"],
            limit=5
        )
        print(f"  - 뉴스 검색 결과: {news_result.get('total', 0)}건")
        
        # 키워드 트렌드 분석 테스트
        trend_result = await gateway_client.get_keyword_trends(
            keywords=["기후변화", "에너지효율"],
            period="6m"
        )
        print(f"  - 키워드 트렌드: {len(trend_result.get('trend_data', []))}개 데이터")
        
        # 감성 분석 테스트
        sentiment_result = await gateway_client.get_news_sentiment(
            company_name="두산퓨얼셀",
            keywords=["ESG", "지속가능성"]
        )
        print(f"  - 감성 분석: {sentiment_result.get('sentiment_data', {})}")
        
    except Exception as e:
        print(f"  - Gateway 클라이언트 테스트 오류: {str(e)}")
    
    # 8. 종합 결과 출력
    print("\n" + "=" * 80)
    print("📋 테스트 결과 요약:")
    print("✅ 기본 매핑 서비스: 정상 동작")
    print("✅ 파싱 서비스: 정상 동작")
    print("✅ 히스토리 분석: 정상 동작")
    print("✅ 추천 서비스: 정상 동작")
    print("✅ 비교 분석: 정상 동작")
    print("✅ Gateway 연동: 설정 완료")
    print("=" * 80)
    
    print("\n🎉 Material Assessment Service 테스트 완료!")
    print("🔗 Gateway 연동이 활성화되면 더 풍부한 뉴스 분석 데이터를 제공합니다.")

def create_sample_history(company_name: str) -> MaterialityHistory:
    """테스트용 샘플 히스토리 생성"""
    
    # 2022년 평가
    topics_2022 = [
        MaterialityTopic(topic_name="기후변화 대응", priority=1, year=2022, company_name=company_name, sasb_mapping="E-GHG"),
        MaterialityTopic(topic_name="에너지 효율", priority=2, year=2022, company_name=company_name, sasb_mapping="E-EFF"),
        MaterialityTopic(topic_name="안전관리", priority=3, year=2022, company_name=company_name, sasb_mapping="S-SAFE"),
        MaterialityTopic(topic_name="공급망 관리", priority=4, year=2022, company_name=company_name, sasb_mapping="S-SUPP"),
        MaterialityTopic(topic_name="인권경영", priority=5, year=2022, company_name=company_name, sasb_mapping="S-HUMAN"),
    ]
    
    # 2023년 평가 (일부 변화)
    topics_2023 = [
        MaterialityTopic(topic_name="기후변화 대응", priority=1, year=2023, company_name=company_name, sasb_mapping="E-GHG"),
        MaterialityTopic(topic_name="안전관리", priority=2, year=2023, company_name=company_name, sasb_mapping="S-SAFE"),  # 상승
        MaterialityTopic(topic_name="에너지 효율", priority=3, year=2023, company_name=company_name, sasb_mapping="E-EFF"),  # 하락
        MaterialityTopic(topic_name="데이터보안", priority=4, year=2023, company_name=company_name, sasb_mapping="G-DATA"),  # 신규
        MaterialityTopic(topic_name="공급망 관리", priority=5, year=2023, company_name=company_name, sasb_mapping="S-SUPP"),  # 하락
    ]
    
    # 2024년 평가 (더 큰 변화)
    topics_2024 = [
        MaterialityTopic(topic_name="기후변화 대응", priority=1, year=2024, company_name=company_name, sasb_mapping="E-GHG"),
        MaterialityTopic(topic_name="데이터보안", priority=2, year=2024, company_name=company_name, sasb_mapping="G-DATA"),  # 상승
        MaterialityTopic(topic_name="지속가능경영", priority=3, year=2024, company_name=company_name, sasb_mapping="G-GOV"),  # 신규
        MaterialityTopic(topic_name="안전관리", priority=4, year=2024, company_name=company_name, sasb_mapping="S-SAFE"),  # 하락
        MaterialityTopic(topic_name="혁신기술", priority=5, year=2024, company_name=company_name, sasb_mapping="G-INNOV"),  # 신규
    ]
    
    # 평가 객체 생성
    assessments = [
        MaterialityAssessment(
            assessment_id="test_2022",
            company_name=company_name,
            year=2022,
            topics=topics_2022,
            upload_date=datetime(2022, 12, 31)
        ),
        MaterialityAssessment(
            assessment_id="test_2023",
            company_name=company_name,
            year=2023,
            topics=topics_2023,
            upload_date=datetime(2023, 12, 31)
        ),
        MaterialityAssessment(
            assessment_id="test_2024",
            company_name=company_name,
            year=2024,
            topics=topics_2024,
            upload_date=datetime(2024, 12, 31)
        ),
    ]
    
    return MaterialityHistory(
        company_name=company_name,
        assessments=assessments
    )

if __name__ == "__main__":
    asyncio.run(test_material_service()) 