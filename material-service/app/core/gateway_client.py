import httpx
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class GatewayClient:
    """Gateway를 통한 마이크로서비스 간 통신 클라이언트"""
    
    def __init__(self):
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8080")
        self.timeout = 30.0
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🔧 Gateway URL 설정: {self.gateway_url}")
    
    async def search_news_by_keywords(
        self, 
        keywords: List[str], 
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """키워드 기반 뉴스 검색 (sasb-service 연동)
        
        Args:
            keywords: 검색 키워드 목록
            date_range: 검색 날짜 범위 {"start": "2023-01-01", "end": "2023-12-31"}
            limit: 검색 결과 수 제한
            
        Returns:
            Dict[str, Any]: 뉴스 검색 결과
        """
        try:
            # 회사명과 SASB 키워드 분리
            company_name = None
            sasb_keywords = keywords
            
            # 첫 번째 키워드가 회사명일 가능성 체크
            if keywords and any(company in keywords[0] for company in ["두산퓨얼셀", "LS ELECTRIC", "SK", "삼성", "LG"]):
                company_name = keywords[0]
                sasb_keywords = keywords[1:] if len(keywords) > 1 else keywords
            
            # sasb-service의 worker 결과 엔드포인트 사용
            if company_name:
                # 회사별 조합 검색 결과
                url = f"{self.gateway_url}/gateway/v1/sasb/api/v1/workers/results/company-combined/{company_name}"
            else:
                # 일반 조합 검색 결과
                url = f"{self.gateway_url}/gateway/v1/sasb/api/v1/workers/results/combined-keywords"
            
            # 쿼리 파라미터 구성
            params: Dict[str, Any] = {
                "max_results": limit
            }
            
            self.logger.info(f"🔍 뉴스 검색 요청: company={company_name}, endpoint={url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # sasb-service 응답 형식을 material-service 형식으로 변환
                    articles = []
                    if "analyzed_articles" in result:
                        for article in result["analyzed_articles"]:
                            # sasb-service 형식을 material-service 기대 형식으로 변환
                            converted_article = {
                                "title": article.get("title", ""),
                                "content": article.get("description", ""),
                                "url": article.get("link", ""),
                                "published_date": article.get("pub_date", "2024-01-01"),  # 기본값 설정
                                "published_at": article.get("pub_date", "2024-01-01T00:00:00"),  # _analyze_news_trend에서 필요
                                "sentiment": self._convert_sentiment(article.get("sentiment", {})),
                                "source": "naver_news",
                                # material-service에서 기대하는 추가 필드들
                                "description": article.get("description", ""),
                                "link": article.get("link", "")
                            }
                            articles.append(converted_article)
                    
                    converted_result = {
                        "results": articles,
                        "total": result.get("total_articles_found", len(articles)),
                        "metadata": {
                            "company_name": company_name,
                            "keywords": sasb_keywords,
                            "analysis_type": result.get("analysis_type", "company_sasb")
                        }
                    }
                    
                    self.logger.info(f"✅ 뉴스 검색 완료: {len(articles)}건")
                    return converted_result
                else:
                    self.logger.error(f"❌ 뉴스 검색 실패: {response.status_code} - {response.text}")
                    return {"results": [], "total": 0, "error": response.text}
                    
        except Exception as e:
            self.logger.error(f"💥 뉴스 검색 중 오류: {str(e)}")
            return {"results": [], "total": 0, "error": str(e)}
    
    def _convert_sentiment(self, sentiment_data: Dict[str, Any]) -> str:
        """sasb-service의 sentiment 데이터를 material-service 형식으로 변환"""
        if not sentiment_data:
            return "neutral"
        
        # sasb-service SentimentResult 구조: {"sentiment": "positive", "confidence": 0.95}
        sentiment_value = sentiment_data.get("sentiment", "").lower()
        
        # 매핑 테이블
        sentiment_mapping = {
            "positive": "positive",
            "negative": "negative", 
            "neutral": "neutral",
            "긍정": "positive",
            "부정": "negative",
            "중립": "neutral",
            "label_0": "negative",
            "label_1": "neutral", 
            "label_2": "positive"
        }
        
        return sentiment_mapping.get(sentiment_value, "neutral")
    
    async def analyze_company_sasb(
        self, 
        company_name: str, 
        keywords: List[str]
    ) -> Dict[str, Any]:
        """기업별 SASB 분석 (sasb-service 연동)
        
        Args:
            company_name: 기업명
            keywords: 분석 키워드 목록
            
        Returns:
            Dict[str, Any]: SASB 분석 결과
        """
        try:
            analysis_request = {
                "company_name": company_name,
                "keywords": keywords,
                "analysis_type": "company_sasb"
            }
            
            url = f"{self.gateway_url}/gateway/v1/sasb/analyze/company-sasb"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=analysis_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"✅ SASB 분석 완료: {company_name}")
                    return result
                else:
                    self.logger.error(f"❌ SASB 분석 실패: {response.status_code} - {response.text}")
                    return {"analysis_result": None, "error": response.text}
                    
        except Exception as e:
            self.logger.error(f"💥 SASB 분석 중 오류: {str(e)}")
            return {"analysis_result": None, "error": str(e)}
    
    async def get_keyword_trends(
        self, 
        keywords: List[str], 
        period: str = "1y"
    ) -> Dict[str, Any]:
        """키워드 트렌드 분석 (sasb-service 연동)
        
        Args:
            keywords: 분석 키워드 목록
            period: 분석 기간 (1m, 3m, 6m, 1y, 2y, 3y)
            
        Returns:
            Dict[str, Any]: 키워드 트렌드 분석 결과
        """
        try:
            trend_request = {
                "keywords": keywords,
                "period": period,
                "analysis_type": "keyword_trends"
            }
            
            url = f"{self.gateway_url}/gateway/v1/sasb/analyze/keyword-trends"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=trend_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"✅ 키워드 트렌드 분석 완료: {len(keywords)}개 키워드")
                    return result
                else:
                    self.logger.error(f"❌ 키워드 트렌드 분석 실패: {response.status_code} - {response.text}")
                    return {"trend_data": [], "error": response.text}
                    
        except Exception as e:
            self.logger.error(f"💥 키워드 트렌드 분석 중 오류: {str(e)}")
            return {"trend_data": [], "error": str(e)}
    
    async def get_news_sentiment(
        self, 
        company_name: str, 
        keywords: List[str]
    ) -> Dict[str, Any]:
        """뉴스 감성 분석 (news-service 연동)
        
        Args:
            company_name: 기업명
            keywords: 감성 분석 키워드 목록
            
        Returns:
            Dict[str, Any]: 감성 분석 결과
        """
        try:
            sentiment_request = {
                "company_name": company_name,
                "keywords": keywords,
                "analysis_type": "sentiment"
            }
            
            url = f"{self.gateway_url}/gateway/v1/news/analyze/sentiment"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=sentiment_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"✅ 감성 분석 완료: {company_name}")
                    return result
                else:
                    self.logger.error(f"❌ 감성 분석 실패: {response.status_code} - {response.text}")
                    return {"sentiment_data": {"positive": 0, "neutral": 0, "negative": 0}, "error": response.text}
                    
        except Exception as e:
            self.logger.error(f"💥 감성 분석 중 오류: {str(e)}")
            return {"sentiment_data": {"positive": 0, "neutral": 0, "negative": 0}, "error": str(e)}
    
    async def get_sasb_health_check(self) -> Dict[str, Any]:
        """SASB 서비스 상태 확인"""
        try:
            url = f"{self.gateway_url}/gateway/v1/sasb/health"
            self.logger.info(f"🔍 SASB 헬스체크 시도: {url}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info("✅ SASB 서비스 연결 정상")
                    return {"status": "healthy", "data": result}
                else:
                    self.logger.error(f"❌ SASB 서비스 연결 실패: {response.status_code}")
                    return {"status": "error", "message": response.text}
                    
        except httpx.ConnectError as e:
            self.logger.error(f"💥 Gateway 연결 실패: {str(e)}")
            return {"status": "error", "message": f"Gateway 연결 실패: {self.gateway_url}"}
        except httpx.TimeoutException as e:
            self.logger.error(f"💥 Gateway 연결 타임아웃: {str(e)}")
            return {"status": "error", "message": "Gateway 연결 타임아웃"}
        except Exception as e:
            self.logger.error(f"💥 SASB 서비스 상태 확인 중 오류: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    # News 서비스는 사용하지 않음 (SASB 서비스만 사용)
    
    async def batch_analyze_topics(
        self, 
        company_name: str, 
        topics: List[str],
        analysis_period: str = "1y"
    ) -> Dict[str, Any]:
        """토픽 배치 분석 (여러 토픽에 대한 종합 분석)
        
        Args:
            company_name: 기업명
            topics: 분석할 토픽 목록
            analysis_period: 분석 기간
            
        Returns:
            Dict[str, Any]: 배치 분석 결과
        """
        try:
            # 각 토픽별로 병렬 분석 수행
            results = {}
            
            for topic in topics:
                # 토픽 관련 키워드 추출
                keywords = self._extract_keywords_from_topic(topic)
                
                # 뉴스 검색
                news_result = await self.search_news_by_keywords(keywords)
                
                # 키워드 트렌드 분석
                trend_result = await self.get_keyword_trends(keywords, analysis_period)
                
                # 감성 분석
                sentiment_result = await self.get_news_sentiment(company_name, keywords)
                
                results[topic] = {
                    "keywords": keywords,
                    "news_count": news_result.get("total", 0),
                    "trend_data": trend_result.get("trend_data", []),
                    "sentiment": sentiment_result.get("sentiment_data", {}),
                    "analysis_period": analysis_period
                }
            
            self.logger.info(f"✅ 배치 분석 완료: {len(topics)}개 토픽")
            return {
                "company_name": company_name,
                "analysis_results": results,
                "summary": self._generate_batch_summary(results)
            }
            
        except Exception as e:
            self.logger.error(f"💥 배치 분석 중 오류: {str(e)}")
            return {"analysis_results": {}, "error": str(e)}
    
    def _extract_keywords_from_topic(self, topic: str) -> List[str]:
        """토픽에서 키워드 추출"""
        # 기본 키워드 매핑 (실제로는 더 정교한 키워드 추출 로직 필요)
        keyword_mapping = {
            "기후변화 대응": ["탄소중립", "온실가스", "기후변화", "RE100"],
            "에너지 효율": ["에너지효율", "절약", "효율개선", "스마트그리드"],
            "안전관리": ["중대재해", "산업안전", "안전보건", "사고예방"],
            "공급망 관리": ["공급망", "협력업체", "SCM", "리스크관리"],
            "지속가능경영": ["ESG", "지속가능성", "사회적책임", "거버넌스"],
            "재생에너지": ["태양광", "풍력", "신재생에너지", "청정에너지"],
            "환경관리": ["환경보호", "폐기물", "오염방지", "환경영향"],
            "인권경영": ["인권", "노동권", "다양성", "포용성"],
            "데이터보안": ["개인정보", "사이버보안", "데이터보호", "정보보안"],
            "혁신기술": ["디지털전환", "AI", "빅데이터", "IoT"]
        }
        
        return keyword_mapping.get(topic, [topic])
    
    def _generate_batch_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """배치 분석 결과 요약 생성"""
        total_news = sum(result.get("news_count", 0) for result in results.values())
        
        # 감성 분석 평균
        sentiment_scores = []
        for result in results.values():
            sentiment = result.get("sentiment", {})
            if sentiment:
                sentiment_scores.append(sentiment)
        
        avg_sentiment = {"positive": 0, "neutral": 0, "negative": 0}
        if sentiment_scores:
            avg_sentiment = {
                "positive": sum(s.get("positive", 0) for s in sentiment_scores) / len(sentiment_scores),
                "neutral": sum(s.get("neutral", 0) for s in sentiment_scores) / len(sentiment_scores),
                "negative": sum(s.get("negative", 0) for s in sentiment_scores) / len(sentiment_scores)
            }
        
        return {
            "total_topics_analyzed": len(results),
            "total_news_analyzed": total_news,
            "average_sentiment": avg_sentiment,
            "most_discussed_topics": sorted(
                results.items(), 
                key=lambda x: x[1].get("news_count", 0), 
                reverse=True
            )[:5]
        } 