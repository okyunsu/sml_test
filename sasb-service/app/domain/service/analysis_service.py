import logging
import random
from typing import List, Optional
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
        🎯 개선된 조합 검색 메서드
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
        all_news_items: List[NewsItem] = []
        
        # 조합 생성 및 제한
        combinations_tried = 0
        
        # 랜덤 샘플링으로 다양한 조합 시도
        sampled_domain = random.sample(domain_keywords, min(3, len(domain_keywords)))
        sampled_issues = random.sample(issue_keywords, min(5, len(issue_keywords)))
        
        logging.info(f"🎯 조합 검색 시작. 회사: {company_name or 'N/A'}")
        logging.info(f"산업 키워드 샘플: {sampled_domain}")
        logging.info(f"이슈 키워드 샘플: {sampled_issues}")

        for domain_keyword in sampled_domain:
            for issue_keyword in sampled_issues:
                if combinations_tried >= max_combinations:
                    break
                    
                # 네이버 API용 AND 조합 쿼리 생성
                if company_name:
                    # 회사 + 산업 키워드 + 이슈 키워드
                    query = f"{company_name} {domain_keyword} {issue_keyword}"
                else:
                    # 산업 키워드 + 이슈 키워드
                    query = f"{domain_keyword} {issue_keyword}"
                
                try:
                    logging.info(f"검색 {combinations_tried + 1}/{max_combinations}: '{query}'")
                    news_items = await self.naver_news_service.search_news(query, display=100)
                    all_news_items.extend(news_items)
                    combinations_tried += 1
                    
                except Exception as e:
                    logging.error(f"'{query}'에 대한 조합 검색 중 오류 발생: {e}", exc_info=True)
            
            if combinations_tried >= max_combinations:
                break

        # 링크를 기준으로 뉴스 기사 중복 제거
        seen_links = set()
        unique_news_items = []
        for item in all_news_items:
            if item.link not in seen_links:
                seen_links.add(item.link)
                unique_news_items.append(item)

        logging.info(f"🎯 조합 검색 완료: 총 {len(all_news_items)}개 수집, 중복 제거 후 {len(unique_news_items)}개 고유 기사")

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
                logging.error(f"조합 검색 기사 분석 중 오류 발생: {e}", exc_info=True)

        logging.info(f"🎯 조합 검색 분석 완료: {len(analyzed_articles)}개 기사 분석됨")
        return analyzed_articles 