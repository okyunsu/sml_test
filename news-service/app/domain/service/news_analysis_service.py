import httpx
import asyncio
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from app.config.settings import settings
from app.domain.model.news_dto import (
    NewsSearchResponse, NewsAnalysisRequest, NewsAnalysisResponse,
    AnalyzedNewsItem, AnalysisSummary, ESGClassification, SentimentAnalysis, NewsItem
)

# ML 추론 서비스 import 시도
try:
    from app.domain.service.ml_inference_service import MLInferenceService
    ML_INFERENCE_AVAILABLE = True
except ImportError:
    ML_INFERENCE_AVAILABLE = False

class NewsAnalysisService:
    """뉴스 분석 서비스 - 파인튜닝된 모델 우선 사용, 폴백으로 외부 ML 서비스 연동"""
    
    def __init__(self):
        self.ml_service_url = settings.ml_service_url
        
        # 로컬 ML 추론 서비스 초기화 시도
        self.local_ml_service = None
        if ML_INFERENCE_AVAILABLE:
            try:
                self.local_ml_service = MLInferenceService()
                print(f"✅ 로컬 ML 추론 서비스 초기화 완료")
            except Exception as e:
                print(f"⚠️ 로컬 ML 추론 서비스 초기화 실패: {str(e)}")
                self.local_ml_service = None
        
        # HTTP 클라이언트 설정 (외부 ML 서비스용)
        self._http_limits = httpx.Limits(
            max_keepalive_connections=10,
            max_connections=50,
            keepalive_expiry=60.0
        )
        
        self._timeout = httpx.Timeout(
            connect=15.0,
            read=120.0,
            write=30.0,
            pool=10.0
        )
    
    @asynccontextmanager
    async def _get_ml_client(self):
        """ML 서비스용 비동기 HTTP 클라이언트"""
        async with httpx.AsyncClient(
            limits=self._http_limits,
            timeout=self._timeout,
            headers={
                "User-Agent": "News-Analysis-Service/1.0",
                "Content-Type": "application/json"
            }
        ) as client:
            yield client
    
    async def analyze_company_news(
        self, 
        company: str, 
        news_response: NewsSearchResponse
    ) -> NewsAnalysisResponse:
        """회사 뉴스 분석 실행 - 비동기 최적화"""
        
        # 빈 뉴스 응답 처리
        if not news_response.items:
            return self._create_empty_analysis_response(company, news_response)
        
        # ML 분석 요청 데이터 생성
        analysis_request = self._create_analysis_request(news_response)
        
        # ML 서비스 호출과 폴백 분석을 동시에 시작 (레이스 조건)
        ml_task = asyncio.create_task(self._call_ml_service_safe(analysis_request))
        fallback_task = asyncio.create_task(self._create_fallback_analysis_async(news_response.items))
        
        # ML 서비스 결과를 기다리되, 타임아웃 시 폴백 사용
        try:
            # ML 서비스를 먼저 시도하고, 실패하면 폴백 사용
            ml_results = await asyncio.wait_for(ml_task, timeout=60.0)
            fallback_task.cancel()  # ML 성공 시 폴백 취소
            ml_service_status = "connected"
        except (asyncio.TimeoutError, Exception):
            ml_task.cancel()  # ML 실패 시 ML 태스크 취소
            ml_results = await fallback_task
            ml_service_status = "fallback"
        
        # 검색 정보 생성
        search_info = self._create_search_info(company, news_response)
        
        return NewsAnalysisResponse(
            search_info=search_info,
            analyzed_news=ml_results["analyzed_news"],
            analysis_summary=ml_results["analysis_summary"],
            ml_service_status=ml_service_status
        )
    
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
        news_data = [
            {
                "title": item.title,
                "description": item.description,
                "link": item.link,
                "pub_date": item.pub_date,
                "mention_count": item.mention_count
            }
            for item in news_response.items
        ]
        
        return NewsAnalysisRequest(news_items=news_data)
    
    async def _call_ml_service_safe(self, analysis_request: NewsAnalysisRequest) -> Dict[str, Any]:
        """안전한 ML 서비스 호출 (예외 처리 포함)"""
        try:
            return await self._call_ml_service(analysis_request)
        except Exception as e:
            # ML 서비스 호출 실패 시 예외 발생
            raise Exception(f"ML service call failed: {str(e)}")
    
    async def _call_ml_service(self, analysis_request: NewsAnalysisRequest) -> Dict[str, Any]:
        """ML 서비스 호출 - 연결 풀 최적화"""
        async with self._get_ml_client() as client:
            response = await client.post(
                f"{self.ml_service_url}/api/v1/ml/analyze-news",
                json=analysis_request.dict()
            )
            response.raise_for_status()
            return response.json()
    
    async def _create_fallback_analysis_async(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """비동기 폴백 분석 - 배치 처리로 최적화"""
        if not news_items:
            return {
                "analyzed_news": [],
                "analysis_summary": AnalysisSummary(
                    total_analyzed=0,
                    esg_distribution={},
                    sentiment_distribution={"긍정": 0, "부정": 0, "중립": 0}
                ).dict()
            }
        
        # 뉴스 아이템들을 배치로 나누어 병렬 처리
        batch_size = 20
        batches = [news_items[i:i + batch_size] for i in range(0, len(news_items), batch_size)]
        
        # 각 배치를 병렬로 분석
        tasks = []
        for batch in batches:
            task = asyncio.create_task(self._analyze_news_batch(batch))
            tasks.append(task)
        
        # 모든 배치 결과를 수집
        batch_results = await asyncio.gather(*tasks)
        
        # 결과 병합
        analyzed_news = []
        for batch_result in batch_results:
            analyzed_news.extend(batch_result)
        
        # 분석 요약 생성
        analysis_summary = await self._create_analysis_summary_async(analyzed_news)
        
        return {
            "analyzed_news": [item.dict() for item in analyzed_news],
            "analysis_summary": analysis_summary.dict()
        }
    
    async def _analyze_news_batch(self, news_batch: List[NewsItem]) -> List[AnalyzedNewsItem]:
        """뉴스 배치 분석 - 로컬 ML 서비스 우선 사용"""
        # I/O 블로킹 방지
        await asyncio.sleep(0)
        
        analyzed_items = []
        for item in news_batch:
            # 텍스트 결합
            text = f"{item.title} {item.description}"
            
            # 로컬 ML 서비스가 사용 가능한 경우 우선 사용
            if self.local_ml_service and self.local_ml_service.is_available():
                try:
                    # 파인튜닝된 모델로 분석
                    category_result = self.local_ml_service.predict_category(text)
                    sentiment_result = self.local_ml_service.predict_sentiment(text)
                    
                    esg_classification = ESGClassification(
                        esg_category=category_result["predicted_label"],
                        confidence_score=category_result["confidence"],
                        keywords=[],  # 파인튜닝 모델에서는 키워드 추출 안함
                        classification_method="fine_tuned_model"
                    )
                    
                    sentiment_analysis = SentimentAnalysis(
                        sentiment=sentiment_result["predicted_label"],
                        confidence_score=sentiment_result["confidence"],
                        positive=sentiment_result["probabilities"].get("긍정", 0.0),
                        negative=sentiment_result["probabilities"].get("부정", 0.0),
                        neutral=sentiment_result["probabilities"].get("중립", 0.0),
                        analysis_method="fine_tuned_model"
                    )
                    
                except Exception as e:
                    print(f"⚠️ 로컬 ML 분석 실패, 폴백 사용: {str(e)}")
                    # 폴백: 키워드 기반 분석
                    esg_task = asyncio.create_task(self._classify_esg_async(text.lower()))
                    sentiment_task = asyncio.create_task(self._analyze_sentiment_async(text.lower()))
                    esg_classification, sentiment_analysis = await asyncio.gather(esg_task, sentiment_task)
            else:
                # 폴백: 키워드 기반 분석
                esg_task = asyncio.create_task(self._classify_esg_async(text.lower()))
                sentiment_task = asyncio.create_task(self._analyze_sentiment_async(text.lower()))
                esg_classification, sentiment_analysis = await asyncio.gather(esg_task, sentiment_task)
            
            analyzed_items.append(AnalyzedNewsItem(
                news_item=item,
                esg_classification=esg_classification,
                sentiment_analysis=sentiment_analysis
            ))
        
        return analyzed_items
    
    async def _classify_esg_async(self, text: str) -> ESGClassification:
        """비동기 ESG 분류"""
        await asyncio.sleep(0)  # 다른 코루틴에게 제어권 양보
        return self._classify_esg_sync(text)
    
    async def _analyze_sentiment_async(self, text: str) -> SentimentAnalysis:
        """비동기 감정 분석"""
        await asyncio.sleep(0)  # 다른 코루틴에게 제어권 양보
        return self._analyze_sentiment_sync(text)
    
    def _classify_esg_sync(self, text: str) -> ESGClassification:
        """동기 ESG 분류 (기존 로직)"""
        esg_keywords = {
            "환경(E)": ["환경", "탄소", "친환경", "재생에너지", "온실가스", "기후변화"],
            "사회(S)": ["사회", "인권", "다양성", "안전", "직원", "고용"],
            "지배구조(G)": ["거버넌스", "윤리", "투명", "컴플라이언스", "이사회"],
            "통합ESG": ["esg", "지속가능", "지속가능성"]
        }
        
        best_category = "기타"
        best_score = 0.0
        matched_keywords = []
        
        for category, keywords in esg_keywords.items():
            matches = [keyword for keyword in keywords if keyword in text]
            if matches:
                score = len(matches) / len(keywords)
                if score > best_score:
                    best_score = score
                    best_category = category
                    matched_keywords = matches
        
        return ESGClassification(
            esg_category=best_category,
            confidence_score=min(best_score + 0.4, 1.0),
            keywords=matched_keywords,
            classification_method="keyword_fallback"
        )
    
    def _analyze_sentiment_sync(self, text: str) -> SentimentAnalysis:
        """동기 감정 분석 (기존 로직)"""
        positive_keywords = ["성장", "증가", "개선", "성공", "발전", "상승", "호조"]
        negative_keywords = ["감소", "하락", "문제", "위험", "손실", "악화", "우려"]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        if positive_count > negative_count:
            sentiment = "긍정"
            positive_score = 0.7
            negative_score = 0.2
            neutral_score = 0.1
        elif negative_count > positive_count:
            sentiment = "부정"
            positive_score = 0.2
            negative_score = 0.7
            neutral_score = 0.1
        else:
            sentiment = "중립"
            positive_score = 0.3
            negative_score = 0.3
            neutral_score = 0.4
        
        confidence = min((abs(positive_count - negative_count) + 1) * 0.2, 1.0)
        
        return SentimentAnalysis(
            sentiment=sentiment,
            confidence_score=confidence,
            positive=positive_score,
            negative=negative_score,
            neutral=neutral_score,
            analysis_method="keyword_fallback"
        )
    
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
            sentiment_distribution[sentiment] += 1
        
        return AnalysisSummary(
            total_analyzed=len(analyzed_news),
            esg_distribution=esg_distribution,
            sentiment_distribution=sentiment_distribution
        ) 