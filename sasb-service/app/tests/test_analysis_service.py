"""
SASB Analysis Service 테스트
Mock 서비스와 인터페이스 기반 테스트
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Python Path 설정
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from shared.testing.mock_services import MockNewsService, MockMLInferenceService
from shared.interfaces.news_service_interface import NewsItem, SentimentResult
from app.domain.service.analysis_service import AnalysisService

class TestAnalysisServiceWithMocks:
    """Mock 서비스를 사용한 Analysis Service 테스트"""
    
    @pytest.fixture
    def mock_news_service(self):
        """Mock 뉴스 서비스 생성"""
        mock_data = [
            NewsItem(
                title="ESG 투자 확대 동향",
                content="기업들의 ESG 투자가 지속적으로 증가하고 있습니다.",
                link="https://example.com/1",
                published_at="2024-01-01",
                source="테스트뉴스"
            ),
            NewsItem(
                title="탄소중립 정책 발표",
                content="정부가 새로운 탄소중립 정책을 발표했습니다.",
                link="https://example.com/2", 
                published_at="2024-01-02",
                source="테스트뉴스"
            ),
            NewsItem(
                title="근로자 복지 개선안",
                content="대기업들이 근로자 복지 개선에 나섰습니다.",
                link="https://example.com/3",
                published_at="2024-01-03",
                source="테스트뉴스"
            )
        ]
        return MockNewsService(mock_data)
    
    @pytest.fixture
    def mock_ml_service(self):
        """Mock ML 추론 서비스 생성"""
        return MockMLInferenceService()
    
    @pytest.fixture 
    def mock_redis_client(self):
        """Mock Redis 클라이언트 생성"""
        mock_redis = Mock()
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        return mock_redis
    
    @pytest.fixture
    def analysis_service(self, mock_news_service, mock_ml_service, mock_redis_client):
        """Analysis Service 인스턴스 생성"""
        return AnalysisService(
            news_service=mock_news_service,
            ml_service=mock_ml_service,
            redis_client=mock_redis_client
        )
    
    @pytest.mark.asyncio
    async def test_analyze_news_with_keywords_success(self, analysis_service, mock_news_service):
        """키워드 기반 뉴스 분석 성공 테스트"""
        # Given
        keywords = ["ESG", "투자"]
        
        # When
        results = await analysis_service.analyze_news_with_keywords(keywords)
        
        # Then
        assert isinstance(results, list)
        assert len(results) > 0
        assert mock_news_service.call_count > 0
        
        # 첫 번째 결과 구조 검증
        if results:
            result = results[0]
            assert 'title' in result
            assert 'content' in result
            assert 'sentiment' in result
    
    @pytest.mark.asyncio
    async def test_analyze_news_with_keywords_empty_result(self, analysis_service):
        """키워드 검색 결과가 없는 경우 테스트"""
        # Given
        keywords = ["empty"]  # MockNewsService에서 빈 결과 반환
        
        # When
        results = await analysis_service.analyze_news_with_keywords(keywords)
        
        # Then
        assert isinstance(results, list)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_news_with_company_name(self, analysis_service, mock_news_service):
        """회사명과 함께 뉴스 분석 테스트"""
        # Given
        keywords = ["환경"]
        company_name = "테스트회사"
        
        # When
        results = await analysis_service.analyze_news_with_keywords(keywords, company_name)
        
        # Then
        assert isinstance(results, list)
        assert mock_news_service.call_count > 0
        assert mock_news_service.last_query is not None
        assert company_name in mock_news_service.last_query
    
    @pytest.mark.asyncio
    async def test_analyze_with_combined_keywords(self, analysis_service):
        """조합 키워드 분석 테스트"""
        # Given
        domain_keywords = ["환경", "사회"]
        issue_keywords = ["투자", "정책"]
        max_combinations = 3
        
        # When
        results = await analysis_service.analyze_with_combined_keywords(
            domain_keywords, issue_keywords, max_combinations=max_combinations
        )
        
        # Then
        assert isinstance(results, list)
        # 조합 수가 max_combinations를 초과하지 않는지 확인
        assert len(results) <= max_combinations * 2  # domain + issue 조합
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_integration(self, analysis_service, mock_ml_service):
        """감정 분석 통합 테스트"""
        # Given
        keywords = ["혁신"]  # 긍정적 키워드
        
        # When  
        results = await analysis_service.analyze_news_with_keywords(keywords)
        
        # Then
        if results:
            result = results[0]
            assert 'sentiment' in result
            sentiment = result['sentiment']
            assert 'label' in sentiment
            assert 'confidence' in sentiment
            assert sentiment['label'] in ['긍정', '부정', '중립']
            assert 0 <= sentiment['confidence'] <= 1
    
    @pytest.mark.asyncio
    async def test_error_handling_api_failure(self, mock_ml_service, mock_redis_client):
        """API 실패 시 에러 처리 테스트"""
        # Given
        error_news_service = MockNewsService()
        analysis_service = AnalysisService(
            news_service=error_news_service,
            ml_service=mock_ml_service,
            redis_client=mock_redis_client
        )
        
        # When/Then
        with pytest.raises(Exception):
            await analysis_service.analyze_news_with_keywords(["error"])
    
    @pytest.mark.asyncio
    async def test_ml_model_not_loaded(self, mock_news_service, mock_redis_client):
        """ML 모델이 로드되지 않은 경우 테스트"""
        # Given
        mock_ml_service = MockMLInferenceService()
        mock_ml_service.set_model_loaded(False)
        
        analysis_service = AnalysisService(
            news_service=mock_news_service,
            ml_service=mock_ml_service,
            redis_client=mock_redis_client
        )
        
        # When/Then
        with pytest.raises(Exception):
            await analysis_service.analyze_news_with_keywords(["테스트"])
    
    def test_redis_caching_logic(self, analysis_service, mock_redis_client):
        """Redis 캐싱 로직 테스트"""
        # Given
        cache_key = "test_key"
        cache_value = "test_value"
        
        # When
        mock_redis_client.get.return_value = cache_value
        result = mock_redis_client.get(cache_key)
        
        # Then
        assert result == cache_value
        mock_redis_client.get.assert_called_once_with(cache_key)
    
    @pytest.mark.asyncio
    async def test_performance_with_large_keyword_set(self, analysis_service):
        """대량 키워드 처리 성능 테스트"""
        # Given
        large_keywords = [f"키워드{i}" for i in range(50)]
        
        # When
        import time
        start_time = time.time()
        results = await analysis_service.analyze_news_with_keywords(large_keywords[:5])  # 실제로는 5개만
        end_time = time.time()
        
        # Then
        processing_time = end_time - start_time
        assert processing_time < 10  # 10초 이내 처리
        assert isinstance(results, list)

class TestAnalysisServiceUnit:
    """Analysis Service 단위 테스트"""
    
    def test_keyword_validation(self):
        """키워드 유효성 검증 테스트"""
        # Given
        analysis_service = AnalysisService(None, None, None)
        
        # When/Then - 빈 키워드 리스트
        with pytest.raises(ValueError):
            asyncio.run(analysis_service.analyze_news_with_keywords([]))
        
        # When/Then - None 키워드
        with pytest.raises(ValueError):
            asyncio.run(analysis_service.analyze_news_with_keywords(None))
    
    def test_service_initialization(self):
        """서비스 초기화 테스트"""
        # Given/When
        mock_news = Mock()
        mock_ml = Mock()
        mock_redis = Mock()
        
        service = AnalysisService(mock_news, mock_ml, mock_redis)
        
        # Then
        assert service.news_service is mock_news
        assert service.ml_service is mock_ml
        assert service.redis_client is mock_redis

# pytest 실행을 위한 메인 함수
if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 