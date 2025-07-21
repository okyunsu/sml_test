"""
Materiality Analysis Service 테스트
의존성 주입과 Mock 서비스를 활용한 종합 테스트
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Python Path 설정
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from shared.testing.mock_services import MockNewsService
from app.domain.service.materiality_analysis_service import MaterialityAnalysisService
from app.domain.model.materiality_dto import MaterialityAssessment, MaterialityTopic

class TestMaterialityAnalysisService:
    """중대성 분석 서비스 테스트"""
    
    @pytest.fixture
    def mock_file_service(self):
        """Mock 파일 서비스"""
        mock_service = Mock()
        mock_service.read_materiality_file = Mock(return_value={
            "company_name": "테스트회사",
            "year": 2024,
            "topics": [
                {"name": "탄소배출", "priority": 9.2, "category": "Environmental"},
                {"name": "근로자안전", "priority": 8.5, "category": "Social"},
                {"name": "지배구조", "priority": 7.8, "category": "Governance"}
            ]
        })
        return mock_service
    
    @pytest.fixture
    def mock_mapping_service(self):
        """Mock 매핑 서비스"""
        mock_service = Mock()
        mock_service.get_sasb_code_by_topic = Mock(return_value="ENV-001")
        mock_service.get_materiality_keywords = Mock(return_value=["탄소", "배출", "온실가스"])
        return mock_service
    
    @pytest.fixture
    def mock_parsing_service(self):
        """Mock 파싱 서비스"""
        mock_service = Mock()
        mock_service.parse_assessment_data = Mock(return_value=MaterialityAssessment(
            company_name="테스트회사",
            year=2024,
            topics=[
                MaterialityTopic(name="탄소배출", priority=9.2, category="Environmental"),
                MaterialityTopic(name="근로자안전", priority=8.5, category="Social")
            ]
        ))
        return mock_service
    
    @pytest.fixture
    def mock_update_engine(self):
        """Mock 업데이트 엔진"""
        mock_engine = Mock()
        mock_engine.analyze_evolution = AsyncMock(return_value={
            "overall_trend": {
                "overall_direction": "increasing",
                "update_necessity": "medium",
                "avg_confidence": 0.75,
                "avg_change_magnitude": 0.15,
                "change_distribution": {"positive": 2, "negative": 1, "neutral": 0}
            },
            "topic_changes": [
                {
                    "topic_name": "탄소배출",
                    "previous_priority": 9.2,
                    "change_magnitude": 0.3,
                    "confidence": 0.85,
                    "change_type": "increase",
                    "reasons": ["뉴스 언급 증가", "정책 강화"]
                }
            ],
            "news_data_summary": {
                "total_articles": 25,
                "analysis_period": "2024-01-01 to 2024-12-31"
            }
        })
        return mock_engine
    
    @pytest.fixture
    def mock_recommendation_service(self):
        """Mock 추천 서비스"""
        mock_service = Mock()
        mock_service.generate_recommendations = Mock(return_value=[
            {
                "type": "priority_review",
                "topic_name": "탄소배출",
                "current_priority": 9.2,
                "suggested_action": "우선순위 상향 검토",
                "rationale": "뉴스 활동 증가 (+0.30)",
                "confidence": 0.85
            }
        ])
        return mock_service
    
    @pytest.fixture
    def analysis_service(self, mock_file_service, mock_mapping_service, mock_parsing_service, 
                        mock_update_engine, mock_recommendation_service):
        """분석 서비스 인스턴스"""
        return MaterialityAnalysisService(
            file_service=mock_file_service,
            mapping_service=mock_mapping_service,
            parsing_service=mock_parsing_service,
            update_engine=mock_update_engine,
            recommendation_service=mock_recommendation_service
        )
    
    @pytest.mark.asyncio
    async def test_analyze_materiality_changes_success(self, analysis_service):
        """중대성 평가 변화 분석 성공 테스트"""
        # Given
        company_name = "테스트회사"
        current_year = 2024
        
        # When
        result = await analysis_service.analyze_materiality_changes(company_name, current_year)
        
        # Then
        assert result is not None
        assert isinstance(result, dict)
        
        # 필수 필드 검증
        assert "analysis_metadata" in result
        assert "news_analysis_summary" in result
        assert "change_analysis" in result
        assert "recommendations" in result
        assert "action_items" in result
        assert "confidence_assessment" in result
        
        # 메타데이터 검증
        metadata = result["analysis_metadata"]
        assert metadata["company_name"] == company_name
        assert metadata["analysis_year"] == current_year
        assert metadata["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_analyze_without_base_assessment(self, analysis_service, mock_file_service):
        """기준 평가 없이 분석하는 경우 테스트"""
        # Given
        mock_file_service.read_materiality_file.return_value = None
        company_name = "신규회사"
        current_year = 2024
        
        # When
        result = await analysis_service.analyze_materiality_changes(company_name, current_year)
        
        # Then
        assert result is not None
        assert result["analysis_metadata"]["analysis_type"] == "news_only_analysis"
        assert "potential_issues" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_during_analysis(self, analysis_service, mock_update_engine):
        """분석 중 에러 발생 시 처리 테스트"""
        # Given
        mock_update_engine.analyze_evolution.side_effect = Exception("분석 엔진 오류")
        
        # When
        result = await analysis_service.analyze_materiality_changes("테스트회사", 2024)
        
        # Then
        assert result is not None
        assert "error_details" in result
        assert result["analysis_metadata"]["status"] == "failure"
    
    def test_generate_change_recommendations_with_high_changes(self, analysis_service):
        """높은 변화가 있는 토픽에 대한 추천 생성 테스트"""
        # Given
        evolution_analysis = {
            "topic_changes": [
                {
                    "topic_name": "탄소배출",
                    "change_magnitude": 0.4,  # 높은 변화
                    "previous_priority": 9.0,
                    "confidence": 0.85,
                    "news_metrics": {"total_articles": 15, "relevant_articles": 12}
                }
            ],
            "overall_trend": {
                "update_necessity": "high",
                "avg_change_magnitude": 0.4,
                "avg_confidence": 0.85
            }
        }
        base_assessment = Mock()
        base_assessment.topics = []
        
        # When
        recommendations = analysis_service._generate_change_recommendations(
            evolution_analysis, base_assessment
        )
        
        # Then
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # 높은 변화 토픽 추천 확인
        high_change_rec = next((r for r in recommendations if r["topic_name"] == "탄소배출"), None)
        assert high_change_rec is not None
        assert high_change_rec["type"] == "priority_review"
    
    def test_generate_priority_suggestions(self, analysis_service):
        """우선순위 변화 제안 생성 테스트"""
        # Given
        evolution_analysis = {
            "topic_changes": [
                {
                    "topic_name": "근로자안전",
                    "previous_priority": 8.0,
                    "change_magnitude": 0.5,  # 상향 변화
                    "confidence": 0.8,
                    "change_type": "increase"
                },
                {
                    "topic_name": "투자정책",
                    "previous_priority": 7.0,
                    "change_magnitude": -0.4,  # 하향 변화
                    "confidence": 0.7,
                    "change_type": "decrease"
                }
            ]
        }
        
        # When
        suggestions = analysis_service._generate_priority_suggestions(evolution_analysis, Mock())
        
        # Then
        assert isinstance(suggestions, list)
        assert len(suggestions) == 2
        
        # 상향 제안 확인
        upward = next((s for s in suggestions if s["topic_name"] == "근로자안전"), None)
        assert upward["suggested_direction"] == "상향 검토"
        
        # 하향 제안 확인
        downward = next((s for s in suggestions if s["topic_name"] == "투자정책"), None)
        assert downward["suggested_direction"] == "하향 검토"
    
    def test_generate_action_items(self, analysis_service):
        """액션 아이템 생성 테스트"""
        # Given
        evolution_analysis = {
            "topic_changes": [
                {"change_magnitude": 0.5},
                {"change_magnitude": 0.3}
            ],
            "overall_trend": {"update_necessity": "high"}
        }
        recommendations = [
            {"confidence": 0.9, "topic_name": "탄소배출"},
            {"confidence": 0.8, "topic_name": "근로자안전"}
        ]
        
        # When
        action_items = analysis_service._generate_action_items(evolution_analysis, recommendations)
        
        # Then
        assert isinstance(action_items, list)
        assert len(action_items) > 0
        
        # 즉시 검토 항목 확인
        immediate_action = next((item for item in action_items if item["priority"] == "immediate"), None)
        assert immediate_action is not None
        
        # 전면 재검토 항목 확인 (높은 업데이트 필요성)
        comprehensive_action = next((item for item in action_items if item["priority"] == "high"), None)
        assert comprehensive_action is not None
    
    def test_assess_overall_confidence(self, analysis_service):
        """전체 신뢰도 평가 테스트"""
        # Given
        evolution_analysis = {
            "overall_trend": {"avg_confidence": 0.8},
            "news_data_summary": {"total_articles": 30}
        }
        
        # When
        confidence_assessment = analysis_service._assess_overall_confidence(evolution_analysis)
        
        # Then
        assert isinstance(confidence_assessment, dict)
        assert "overall_confidence" in confidence_assessment
        assert "confidence_level" in confidence_assessment
        assert "limitations" in confidence_assessment
        
        assert confidence_assessment["overall_confidence"] == 0.8
        assert confidence_assessment["confidence_level"] in ["high", "medium", "low"]
        assert isinstance(confidence_assessment["limitations"], list)

class TestMaterialityAnalysisIntegration:
    """통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow_with_mocked_dependencies(self):
        """의존성 주입된 완전한 분석 워크플로우 테스트"""
        # Given - 모든 의존성을 Mock으로 설정
        mock_services = {}
        for service_name in ['file_service', 'mapping_service', 'parsing_service', 
                           'update_engine', 'recommendation_service']:
            mock_services[service_name] = Mock()
        
        # Mock 데이터 설정
        mock_services['file_service'].read_materiality_file.return_value = {"company_name": "테스트회사"}
        mock_services['parsing_service'].parse_assessment_data.return_value = Mock()
        mock_services['update_engine'].analyze_evolution = AsyncMock(return_value={
            "overall_trend": {"overall_direction": "stable", "update_necessity": "low", 
                            "avg_confidence": 0.6, "avg_change_magnitude": 0.1,
                            "change_distribution": {"positive": 1, "negative": 0, "neutral": 2}},
            "topic_changes": [],
            "news_data_summary": {"total_articles": 10, "analysis_period": "2024"}
        })
        
        # 서비스 인스턴스 생성
        analysis_service = MaterialityAnalysisService(**mock_services)
        
        # When
        result = await analysis_service.analyze_materiality_changes("테스트회사", 2024)
        
        # Then
        assert result is not None
        assert result["analysis_metadata"]["status"] == "success"
        
        # 모든 의존성이 호출되었는지 확인
        mock_services['file_service'].read_materiality_file.assert_called_once()
        mock_services['update_engine'].analyze_evolution.assert_called_once()

# pytest 실행을 위한 메인 함수
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 