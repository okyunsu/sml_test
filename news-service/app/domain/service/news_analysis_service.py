"""리팩토링된 뉴스 분석 서비스"""
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.domain.model.news_dto import (
    NewsSearchResponse, NewsAnalysisRequest, NewsAnalysisResponse,
    AnalyzedNewsItem, AnalysisSummary, ESGClassification, SentimentAnalysis, NewsItem
)
from app.core.http_client import HttpClientManager, MLHttpClientConfig
from app.config.ml_settings import ml_processing_settings
from app.domain.model.ml_strategies import (
    KeywordBasedESGStrategy, KeywordBasedSentimentStrategy, AnalysisContext
)

# ML 추론 서비스 import 시도
try:
    from app.domain.service.ml_inference_service import MLInferenceService
    ML_INFERENCE_AVAILABLE = True
except ImportError:
    MLInferenceService = None  # type: ignore
    ML_INFERENCE_AVAILABLE = False

class NewsAnalysisService:
    """뉴스 분석 서비스 - 리팩토링 완료"""
    
    def __init__(self):
        self.ml_service_url = settings.ml_service_url
        
        # HTTP 클라이언트 매니저 초기화
        self.http_manager = HttpClientManager(MLHttpClientConfig())
        
        # 로컬 ML 추론 서비스 - 의존성 주입 사용
        self.local_ml_service = self._get_ml_service_from_container()
        
        # 폴백 분석 전략 초기화
        self.fallback_analysis = AnalysisContext(
            KeywordBasedESGStrategy(),
            KeywordBasedSentimentStrategy()
        )
    
    def _get_ml_service_from_container(self) -> Optional[Any]:
        """의존성 주입 컨테이너에서 ML 추론 서비스 가져오기"""
        if not ML_INFERENCE_AVAILABLE:
            return None
            
        try:
            from app.core.dependencies import get_dependency
            container = get_dependency()
            service = container.get("ml_inference_service")
            print(f"✅ 의존성 주입에서 ML 추론 서비스 가져오기 완료")
            return service
        except Exception as e:
            print(f"⚠️ ML 추론 서비스 가져오기 실패: {str(e)}")
            return None
    
    async def analyze_company_news(
        self, 
        company: str, 
        news_response: NewsSearchResponse
    ) -> NewsAnalysisResponse:
        """회사 뉴스 분석 실행"""
        
        if not news_response.items:
            return self._create_empty_analysis_response(company, news_response)
        
        # 분석 실행
        analysis_results = await self._execute_analysis_with_fallback(news_response)
        
        # 검색 정보 생성
        search_info = self._create_search_info(company, news_response)
        
        return NewsAnalysisResponse(
            search_info=search_info,
            analyzed_news=analysis_results["analyzed_news"],
            analysis_summary=analysis_results["analysis_summary"],
            ml_service_status=analysis_results["service_status"]
        )
    
    async def _execute_analysis_with_fallback(self, news_response: NewsSearchResponse) -> Dict[str, Any]:
        """분석 실행 및 폴백 처리"""
        # 우선순위: 로컬 ML 서비스 > 외부 ML 서비스 > 키워드 기반 폴백
        
        # 1. 로컬 ML 서비스 시도
        if self.local_ml_service and self.local_ml_service.is_available():
            try:
                return await self._analyze_with_local_ml_service(news_response)
            except Exception as e:
                print(f"⚠️ 로컬 ML 서비스 실패, 외부 서비스 시도: {str(e)}")
        
        # 2. 외부 ML 서비스와 폴백 경쟁
        return await self._race_external_ml_vs_fallback(news_response)
    
    async def _analyze_with_local_ml_service(self, news_response: NewsSearchResponse) -> Dict[str, Any]:
        """로컬 ML 서비스로 분석"""
        print(f"📊 로컬 ML 서비스로 뉴스 분석 시작: {len(news_response.items)}개 아이템")
        
        try:
            analyzed_news = await self._analyze_news_batch_local(news_response.items)
            print(f"✅ 로컬 ML 서비스 분석 완료: {len(analyzed_news)}개 결과")
            
            analysis_summary = await self._create_analysis_summary_async(analyzed_news)
            
            return {
                "analyzed_news": [item.dict() for item in analyzed_news],
                "analysis_summary": analysis_summary.dict(),
                "service_status": "local_ml"
            }
        except Exception as e:
            print(f"❌ 로컬 ML 서비스 분석 실패: {str(e)}")
            raise
    
    async def _race_external_ml_vs_fallback(self, news_response: NewsSearchResponse) -> Dict[str, Any]:
        """외부 ML 서비스와 폴백 분석 경쟁"""
        print(f"🏁 외부 ML vs 폴백 분석 경쟁 시작: {len(news_response.items)}개 아이템")
        
        analysis_request = self._create_analysis_request(news_response)
        
        # 외부 ML 서비스와 폴백 분석을 동시에 시작
        ml_task = asyncio.create_task(self._call_external_ml_service_safe(analysis_request))
        fallback_task = asyncio.create_task(self._create_fallback_analysis_async(news_response.items))
        
        try:
            # 외부 ML 서비스를 먼저 시도 (60초 타임아웃)
            print("🌐 외부 ML 서비스 시도 중...")
            ml_results = await asyncio.wait_for(ml_task, timeout=60.0)
            fallback_task.cancel()
            print("✅ 외부 ML 서비스 성공")
            return {**ml_results, "service_status": "external_ml"}
        except (asyncio.TimeoutError, Exception) as e:
            print(f"⚠️ 외부 ML 서비스 실패 ({str(e)}), 폴백 분석 사용")
            ml_task.cancel()
            fallback_results = await fallback_task
            print("✅ 폴백 분석 완료")
            return {**fallback_results, "service_status": "fallback"}
    
    async def _analyze_news_batch_local(self, news_items: List[NewsItem]) -> List[AnalyzedNewsItem]:
        """로컬 ML 서비스로 뉴스 배치 분석 (성능 최적화)"""
        if not self.local_ml_service:
            print("❌ 로컬 ML 서비스를 사용할 수 없음")
            return []
        
        # 최적 배치 크기 (성능 개선을 위해 더 큰 배치 사용)
        optimal_batch_size = 32  # 10 → 32로 증가 (GPU 활용도 극대화)
        
        if len(news_items) > optimal_batch_size:
            print(f"📦 고성능 배치 처리: {len(news_items)}개를 {optimal_batch_size}개씩 나누어 처리")
            
            analyzed_items = []
            for i in range(0, len(news_items), optimal_batch_size):
                batch = news_items[i:i + optimal_batch_size]
                batch_num = i // optimal_batch_size + 1
                total_batches = (len(news_items) + optimal_batch_size - 1) // optimal_batch_size
                
                print(f"  🚀 배치 {batch_num}/{total_batches} 고속 처리: {len(batch)}개 아이템")
                
                batch_results = await self._process_single_batch_local(batch)
                analyzed_items.extend(batch_results)
                
                print(f"  ⚡ 배치 {batch_num}/{total_batches} 완료: {len(batch_results)}개 결과")
            
            return analyzed_items
        else:
            print(f"🚀 단일 배치 고속 처리: {len(news_items)}개 아이템")
            return await self._process_single_batch_local(news_items)
    
    async def _process_single_batch_local(self, news_items: List[NewsItem]) -> List[AnalyzedNewsItem]:
        """단일 배치 처리"""
        # ML 서비스 사용 가능성 재확인
        if not self.local_ml_service or not self.local_ml_service.is_available():
            print("❌ ML 서비스를 사용할 수 없음")
            return []
        
        # 타입 체커를 위한 확실한 타입 가드
        assert self.local_ml_service is not None
        
        # 뉴스 아이템을 딕셔너리 형태로 변환
        news_data = [self._news_item_to_dict(item) for item in news_items]
        
        # 로컬 ML 서비스로 분석
        try:
            print(f"🔄 ML 추론 서비스 호출: {len(news_data)}개 아이템")
            results = await self.local_ml_service.analyze_news_batch(news_data)
            print(f"✅ ML 추론 완료: {len(results)}개 결과")
        except Exception as e:
            print(f"❌ ML 추론 서비스 오류: {str(e)}")
            raise
        
        # 결과를 AnalyzedNewsItem으로 변환
        analyzed_items = []
        for i, result in enumerate(results):
            try:
                analyzed_item = self._convert_ml_result_to_analyzed_item(result, news_items)
                if analyzed_item:
                    analyzed_items.append(analyzed_item)
            except Exception as e:
                print(f"⚠️ 결과 변환 실패 (아이템 {i+1}): {str(e)}")
        
        return analyzed_items
    
    def _news_item_to_dict(self, item: NewsItem) -> Dict[str, Any]:
        """NewsItem을 딕셔너리로 변환"""
        return {
            "title": item.title,
            "description": item.description,
            "link": item.link,
            "pub_date": item.pub_date,
            "mention_count": item.mention_count
        }
    
    def _convert_ml_result_to_analyzed_item(
        self, 
        result: Dict[str, Any], 
        original_items: List[NewsItem]
    ) -> Optional[AnalyzedNewsItem]:
        """ML 결과를 AnalyzedNewsItem으로 변환"""
        try:
            # 원본 뉴스 아이템 찾기
            original_item = self._find_original_news_item(result, original_items)
            if not original_item:
                return None
            
            # ESG 분류 정보 변환
            esg_info = result.get("esg_classification", {})
            esg_classification = ESGClassification(
                esg_category=esg_info.get("category", "기타"),
                confidence_score=esg_info.get("confidence", 0.0),
                keywords=[],
                classification_method=esg_info.get("classification_method", "unknown")
            )
            
            # 감정 분석 정보 변환
            sentiment_info = result.get("sentiment_analysis", {})
            probabilities = sentiment_info.get("probabilities", {})
            sentiment_analysis = SentimentAnalysis(
                sentiment=sentiment_info.get("sentiment", "중립"),
                confidence_score=sentiment_info.get("confidence", 0.0),
                positive=probabilities.get("긍정", 0.0),
                negative=probabilities.get("부정", 0.0),
                neutral=probabilities.get("중립", 0.0),
                analysis_method=sentiment_info.get("classification_method", "unknown")
            )
            
            return AnalyzedNewsItem(
                news_item=original_item,
                esg_classification=esg_classification,
                sentiment_analysis=sentiment_analysis
            )
            
        except Exception as e:
            print(f"ML 결과 변환 중 오류: {str(e)}")
            return None
    
    def _find_original_news_item(
        self, 
        result: Dict[str, Any], 
        original_items: List[NewsItem]
    ) -> Optional[NewsItem]:
        """ML 결과에 해당하는 원본 뉴스 아이템 찾기"""
        result_title = result.get("title", "")
        result_link = result.get("link", "")
        
        for item in original_items:
            if item.title == result_title or item.link == result_link:
                return item
        
        return None
    
    async def _call_external_ml_service_safe(self, analysis_request: NewsAnalysisRequest) -> Dict[str, Any]:
        """안전한 외부 ML 서비스 호출"""
        try:
            return await self._call_external_ml_service(analysis_request)
        except Exception as e:
            raise Exception(f"External ML service call failed: {str(e)}")
    
    async def _call_external_ml_service(self, analysis_request: NewsAnalysisRequest) -> Dict[str, Any]:
        """외부 ML 서비스 호출"""
        headers = {"Content-Type": "application/json"}
        
        async with self.http_manager.get_client(headers) as client:
            response = await client.post(
                f"{self.ml_service_url}/api/v1/ml/analyze-news",
                json=analysis_request.dict()
            )
            response.raise_for_status()
            return response.json()
    
    async def _create_fallback_analysis_async(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """키워드 기반 폴백 분석"""
        if not news_items:
            return self._create_empty_analysis_result()
        
        # 배치 처리로 최적화
        analyzed_news = await self._analyze_news_batch_fallback(news_items)
        analysis_summary = await self._create_analysis_summary_async(analyzed_news)
        
        return {
            "analyzed_news": [item.dict() for item in analyzed_news],
            "analysis_summary": analysis_summary.dict()
        }
    
    async def _analyze_news_batch_fallback(self, news_items: List[NewsItem]) -> List[AnalyzedNewsItem]:
        """키워드 기반 배치 분석"""
        # 배치로 나누어 병렬 처리
        batches = self._create_batches(news_items, ml_processing_settings.batch_size)
        
        # 각 배치를 병렬로 분석
        tasks = [
            asyncio.create_task(self._analyze_batch_with_fallback(batch))
            for batch in batches
        ]
        
        batch_results = await asyncio.gather(*tasks)
        
        # 결과 병합
        analyzed_news = []
        for batch_result in batch_results:
            analyzed_news.extend(batch_result)
        
        return analyzed_news
    
    def _create_batches(self, items: List[NewsItem], batch_size: int) -> List[List[NewsItem]]:
        """아이템을 배치로 나누기"""
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    async def _analyze_batch_with_fallback(self, news_batch: List[NewsItem]) -> List[AnalyzedNewsItem]:
        """폴백 전략으로 배치 분석"""
        await asyncio.sleep(0)  # I/O 블로킹 방지
        
        analyzed_items = []
        for item in news_batch:
            text = f"{item.title} {item.description}".lower()
            
            # 분석 수행
            analysis_result = await self.fallback_analysis.analyze_text(text)
            
            # ESG 분류
            esg_data = analysis_result["esg"]
            esg_classification = ESGClassification(
                esg_category=esg_data["category"],
                confidence_score=esg_data["confidence"],
                keywords=esg_data.get("keywords", []),
                classification_method=esg_data["method"]
            )
            
            # 감정 분석
            sentiment_data = analysis_result["sentiment"]
            sentiment_analysis = SentimentAnalysis(
                sentiment=sentiment_data["sentiment"],
                confidence_score=sentiment_data["confidence"],
                positive=sentiment_data["positive"],
                negative=sentiment_data["negative"],
                neutral=sentiment_data["neutral"],
                analysis_method=sentiment_data["method"]
            )
            
            analyzed_items.append(AnalyzedNewsItem(
                news_item=item,
                esg_classification=esg_classification,
                sentiment_analysis=sentiment_analysis
            ))
        
        return analyzed_items
    
    def _create_empty_analysis_response(self, company: str, news_response: NewsSearchResponse) -> NewsAnalysisResponse:
        """빈 분석 응답 생성"""
        search_info = self._create_search_info(company, news_response)
        empty_summary = AnalysisSummary(
            total_analyzed=0,
            esg_distribution={},
            sentiment_distribution={"긍정": 0, "부정": 0, "중립": 0}
        )
        
        return NewsAnalysisResponse(
            search_info=search_info,
            analyzed_news=[],
            analysis_summary=empty_summary,
            ml_service_status="no_data"
        )
    
    def _create_empty_analysis_result(self) -> Dict[str, Any]:
        """빈 분석 결과 생성"""
        empty_summary = AnalysisSummary(
            total_analyzed=0,
            esg_distribution={},
            sentiment_distribution={"긍정": 0, "부정": 0, "중립": 0}
        )
        
        return {
            "analyzed_news": [],
            "analysis_summary": empty_summary.dict()
        }
    
    def _create_search_info(self, company: str, news_response: NewsSearchResponse) -> Dict[str, Any]:
        """검색 정보 생성"""
        return {
            "company": company,
            "total": news_response.total,
            "start": news_response.start,
            "display": news_response.display,
            "last_build_date": news_response.last_build_date,
            "original_count": news_response.original_count,
            "duplicates_removed": news_response.duplicates_removed,
            "deduplication_enabled": news_response.deduplication_enabled
        }
    
    def _create_analysis_request(self, news_response: NewsSearchResponse) -> NewsAnalysisRequest:
        """ML 분석을 위한 요청 데이터 생성"""
        news_data = [self._news_item_to_dict(item) for item in news_response.items]
        return NewsAnalysisRequest(news_items=news_data)
    
    async def _create_analysis_summary_async(self, analyzed_news: List[AnalyzedNewsItem]) -> AnalysisSummary:
        """비동기 분석 요약 생성"""
        await asyncio.sleep(0)  # 다른 코루틴에게 제어권 양보
        
        esg_distribution = {}
        sentiment_distribution = {"긍정": 0, "부정": 0, "중립": 0}
        
        for item in analyzed_news:
            # ESG 분포
            category = item.esg_classification.esg_category
            esg_distribution[category] = esg_distribution.get(category, 0) + 1
            
            # 감정 분포
            sentiment = item.sentiment_analysis.sentiment
            if sentiment in sentiment_distribution:
                sentiment_distribution[sentiment] += 1
        
        return AnalysisSummary(
            total_analyzed=len(analyzed_news),
            esg_distribution=esg_distribution,
            sentiment_distribution=sentiment_distribution
        ) 