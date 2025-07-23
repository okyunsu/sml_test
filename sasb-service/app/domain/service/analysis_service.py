import logging
import random
import os
import sys
from typing import List, Optional

# ✅ Python Path 설정 (shared 모듈 접근용)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

# ✅ 공통 뉴스 검색 헬퍼 사용
from shared.services.news_search_helper import NewsSearchHelper

from .naver_news_service import NaverNewsService
from .ml_inference_service import MLInferenceService
from ..model.sasb_dto import AnalyzedNewsArticle, NewsItem, SentimentResult

class AnalysisService:
    """
    Orchestrates the news analysis workflow:
    1. Fetches news from Naver based on keywords.
    2. Deduplicates articles.
    3. Analyzes sentiment for each unique article.
    4. Returns a list of analyzed articles.
    """
    def __init__(self):
        self.naver_news_service = NaverNewsService()
        self.ml_inference_service = MLInferenceService()

    async def analyze_and_cache_news(
        self, 
        keywords: List[str], 
        company_name: Optional[str] = None
    ) -> List[AnalyzedNewsArticle]:
        """
        Generic method to fetch, deduplicate, and analyze news for a list of keywords
        and an optional company name.
        """
        all_news_items: List[NewsItem] = []
        logging.info(f"분석 시작. 회사: {company_name or 'N/A'}, 키워드: {keywords}")

        for keyword in keywords:
            query = f"{company_name} {keyword}" if company_name else keyword
            try:
                # Corrected method name from get_news to search_news
                news_items = await self.naver_news_service.search_news(query, display=100)
                all_news_items.extend(news_items)
            except Exception as e:
                logging.error(f"'{query}'에 대한 뉴스 검색 중 오류 발생: {e}", exc_info=True)

        # 링크를 기준으로 뉴스 기사 중복 제거
        seen_links = set()
        unique_news_items = []
        for item in all_news_items:
            if item.link not in seen_links:
                seen_links.add(item.link)
                unique_news_items.append(item)

        logging.info(f"총 {len(all_news_items)}개의 기사 수집, 중복 제거 후 {len(unique_news_items)}개의 고유 기사 발견.")

        # 감성 분석
        analyzed_articles = []
        for news_item in unique_news_items:
            try:
                sentiment_result = self.ml_inference_service.analyze_sentiment(news_item.title)
                analyzed_article = AnalyzedNewsArticle(
                    title=news_item.title,
                    link=news_item.link,
                    description=news_item.description,
                    sentiment=SentimentResult(**sentiment_result)
                )
                analyzed_articles.append(analyzed_article)
            except Exception as e:
                logging.error(f"기사 분석 중 오류 발생: {e}", exc_info=True)

        logging.info(f"{len(analyzed_articles)}개의 기사에 대한 분석 완료.")
        return analyzed_articles

    async def analyze_with_combined_keywords(
        self,
        domain_keywords: List[str],
        issue_keywords: List[str], 
        company_name: Optional[str] = None,
        max_combinations: int = 5
    ) -> List[AnalyzedNewsArticle]:
        """
        🎯 개선된 조합 검색 메서드 (리팩토링됨)
        (산업 키워드) AND (SASB 이슈 키워드) 조합으로 검색하여 
        관련성 높은 뉴스만 수집
        
        Args:
            domain_keywords: 신재생에너지 산업/분야 키워드 
            issue_keywords: SASB 이슈 키워드
            company_name: 회사명 (선택적)
            max_combinations: 최대 조합 수 (너무 많은 API 호출 방지)
        
        Returns:
            분석된 뉴스 기사 리스트
        """
        logging.info(f"🎯 조합 검색 시작. 회사: {company_name or 'N/A'}")
        
        # 1. 키워드 샘플링 (공통 헬퍼 사용)
        sampled_domain, sampled_issues = NewsSearchHelper.sample_keywords(
            domain_keywords, issue_keywords, max_domain=3, max_issues=5
        )
        
        logging.info(f"산업 키워드 샘플: {sampled_domain}")
        logging.info(f"이슈 키워드 샘플: {sampled_issues}")
        
        # 2. 검색 쿼리 생성 (공통 헬퍼 사용)
        search_queries = NewsSearchHelper.generate_search_queries(
            sampled_domain, sampled_issues, company_name, max_combinations
        )
        
        # 3. 뉴스 검색 실행 (키워드 정보 포함)
        all_news_items_with_keywords = await self._search_news_with_queries_tracked(search_queries)
        
        # 4. 중복 제거 (키워드 정보 유지)
        unique_news_with_keywords = self._deduplicate_with_keyword_tracking(all_news_items_with_keywords)
        
        # 5. 감정 분석 (키워드 정보 포함)
        analyzed_articles = await self._analyze_sentiment_for_articles_with_keywords(unique_news_with_keywords)
        
        logging.info(f"🎯 조합 검색 분석 완료: {len(analyzed_articles)}개 기사 분석됨")
        return analyzed_articles
    
    async def _search_news_with_queries(self, queries: List[str]) -> List[NewsItem]:
        """쿼리 리스트로 뉴스 검색 실행"""
        all_news_items: List[NewsItem] = []
        
        for i, query in enumerate(queries):
            try:
                logging.info(f"검색 {i + 1}/{len(queries)}: '{query}'")
                news_items = await self.naver_news_service.search_news(query, display=100)
                all_news_items.extend(news_items)
            except Exception as e:
                logging.error(f"'{query}'에 대한 조합 검색 중 오류 발생: {e}", exc_info=True)
        
        logging.info(f"총 {len(all_news_items)}개 뉴스 수집 완료")
        return all_news_items
    
    async def _search_news_with_queries_tracked(self, queries: List[str]) -> List[dict]:
        """
        쿼리 리스트로 뉴스 검색 실행 (키워드 정보 추적)
        
        Returns:
            List[dict]: [{"news_item": NewsItem, "search_query": str, "keywords": List[str]}]
        """
        all_news_items_with_keywords = []
        
        for i, query in enumerate(queries):
            try:
                logging.info(f"🔍 검색 {i + 1}/{len(queries)}: '{query}'")
                news_items = await self.naver_news_service.search_news(query, display=100)
                
                # 쿼리에서 키워드 추출 (공백으로 분리)
                keywords = query.split()
                
                # 각 뉴스 아이템에 키워드 정보 추가
                for news_item in news_items:
                    news_with_keywords = {
                        "news_item": news_item,
                        "search_query": query,
                        "keywords": keywords
                    }
                    all_news_items_with_keywords.append(news_with_keywords)
                    
            except Exception as e:
                logging.error(f"'{query}'에 대한 조합 검색 중 오류 발생: {e}", exc_info=True)
        
        logging.info(f"🔍 총 {len(all_news_items_with_keywords)}개 뉴스 (키워드 정보 포함) 수집 완료")
        return all_news_items_with_keywords
    
    def _deduplicate_with_keyword_tracking(self, news_with_keywords: List[dict]) -> List[dict]:
        """
        🎯 유사도 기반 키워드 정보를 유지하면서 중복 제거
        
        Args:
            news_with_keywords: [{"news_item": NewsItem, "search_query": str, "keywords": List[str]}]
        
        Returns:
            List[dict]: [{"news_item": NewsItem, "matched_keywords": List[str]}] (중복 제거됨)
        """
        unique_news_with_keywords = []
        similarity_threshold = 0.6
        
        for current_item_data in news_with_keywords:
            current_item = current_item_data["news_item"]
            current_keywords = current_item_data["keywords"]
            current_text = NewsSearchHelper._extract_article_text({
                'title': current_item.title,
                'description': current_item.description,
                'content': getattr(current_item, 'content', '')
            })
            
            # 기존 고유 기사들과 유사도 비교
            found_similar = False
            for unique_item_data in unique_news_with_keywords:
                unique_item = unique_item_data["news_item"]
                unique_text = NewsSearchHelper._extract_article_text({
                    'title': unique_item.title,
                    'description': unique_item.description,
                    'content': getattr(unique_item, 'content', '')
                })
                
                similarity = NewsSearchHelper._calculate_text_similarity(current_text, unique_text)
                
                if similarity >= similarity_threshold:
                    # 유사한 기사 발견 -> 키워드 병합
                    unique_item_data["matched_keywords"].extend(current_keywords)
                    unique_item_data["matched_keywords"] = list(set(unique_item_data["matched_keywords"]))  # 중복 제거
                    found_similar = True
                    logging.debug(f"🎯 유사 기사 병합: 유사도 {similarity:.2f}")
                    break
            
            if not found_similar:
                # 새로운 고유 기사 추가
                unique_news_with_keywords.append({
                    "news_item": current_item,
                    "matched_keywords": current_keywords.copy()
                })
        
        logging.info(f"🎯 유사도 기반 중복 제거 완료: {len(news_with_keywords)}개 → {len(unique_news_with_keywords)}개 고유 기사 (키워드 정보 유지)")
        return unique_news_with_keywords
    
    async def _analyze_sentiment_for_articles_with_keywords(self, news_with_keywords: List[dict]) -> List[AnalyzedNewsArticle]:
        """
        뉴스 기사들에 대한 감정 분석 수행 (키워드 정보 포함)
        
        Args:
            news_with_keywords: [{"news_item": NewsItem, "matched_keywords": List[str]}]
        
        Returns:
            List[AnalyzedNewsArticle]: matched_keywords 필드 포함
        """
        analyzed_articles = []
        
        for item_data in news_with_keywords:
            news_item = item_data["news_item"]
            matched_keywords = item_data["matched_keywords"]
            
            try:
                sentiment_result = self.ml_inference_service.analyze_sentiment(news_item.title)
                analyzed_article = AnalyzedNewsArticle(
                    title=news_item.title,
                    link=news_item.link,
                    description=news_item.description,
                    sentiment=SentimentResult(**sentiment_result),
                    matched_keywords=matched_keywords  # 🎯 키워드 정보 포함!
                )
                analyzed_articles.append(analyzed_article)
            except Exception as e:
                logging.error(f"기사 분석 중 오류 발생 (키워드: {matched_keywords}): {e}", exc_info=True)
        
        logging.info(f"🎯 {len(analyzed_articles)}개 기사 감정 분석 완료 (키워드 정보 포함)")
        return analyzed_articles
    
    async def _analyze_sentiment_for_articles(self, news_items: List[NewsItem]) -> List[AnalyzedNewsArticle]:
        """뉴스 기사들에 대한 감정 분석 수행"""
        analyzed_articles = []
        
        for news_item in news_items:
            try:
                sentiment_result = self.ml_inference_service.analyze_sentiment(news_item.title)
                analyzed_article = AnalyzedNewsArticle(
                    title=news_item.title,
                    link=news_item.link,
                    description=news_item.description,
                    sentiment=SentimentResult(**sentiment_result)
                )
                analyzed_articles.append(analyzed_article)
            except Exception as e:
                logging.error(f"기사 분석 중 오류 발생: {e}", exc_info=True)
        
        logging.info(f"{len(analyzed_articles)}개 기사 감정 분석 완료")
        return analyzed_articles
    
    def _convert_news_item_to_dict(self, news_item: NewsItem) -> dict:
        """NewsItem을 dict로 변환 (중복 제거용)"""
        return {
            'title': news_item.title,
            'link': news_item.link,
            'description': news_item.description
        }
    
    def _convert_dict_to_news_item(self, news_dict: dict) -> NewsItem:
        """dict를 NewsItem으로 변환"""
        return NewsItem(
            title=news_dict['title'],
            link=news_dict['link'],
            description=news_dict['description']
        ) 