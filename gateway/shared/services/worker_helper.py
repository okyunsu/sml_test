"""
워커 헬퍼 모듈
SASB Worker에서 사용하는 복잡한 분석 로직을 지원하는 헬퍼 함수들
"""
import asyncio
import json
import logging
from typing import List, Optional, Dict, Any, Set

logger = logging.getLogger(__name__)

class DualSearchHelper:
    """이중 검색 분석 헬퍼 클래스"""
    
    @staticmethod
    def get_current_keyword_index(redis_client, index_redis_key: str, keyword_list: List[str]) -> tuple:
        """현재 키워드 인덱스와 키워드 반환"""
        current_index_str = redis_client.get(index_redis_key)
        current_index = int(current_index_str) if current_index_str else 0
        keyword_to_search = keyword_list[current_index]
        
        logger.info(f"현재 키워드 인덱스: {current_index}, 키워드: '{keyword_to_search}'")
        return current_index, keyword_to_search
    
    @staticmethod
    async def execute_company_sasb_search(
        analysis_service, 
        keyword: str, 
        companies: List[str]
    ) -> List[Dict[str, Any]]:
        """회사 + SASB 키워드 조합 검색 실행"""
        all_articles = []
        
        for company in companies:
            logger.info(f"회사+SASB 검색: {company} + {keyword}")
            
            # async_analyze_and_cache_news 함수 호출 (실제 구현은 서비스에 따라 다름)
            company_sasb_articles = await DualSearchHelper._analyze_and_cache_news(
                analysis_service, keywords=[keyword], company_name=company
            )
            
            # 메타데이터 추가
            for article in company_sasb_articles:
                article_dict = article.dict() if hasattr(article, 'dict') else dict(article)
                article_dict['search_type'] = 'company_sasb'
                article_dict['company'] = company
                all_articles.append(article_dict)
        
        logger.info(f"회사+SASB 검색 완료: {len(all_articles)}개 기사")
        return all_articles
    
    @staticmethod
    async def execute_sasb_only_search(
        analysis_service, 
        keyword: str
    ) -> List[Dict[str, Any]]:
        """SASB 키워드 전용 검색 실행"""
        logger.info(f"SASB 전용 검색: {keyword}")
        
        sasb_only_articles = await DualSearchHelper._analyze_and_cache_news(
            analysis_service, keywords=[keyword], company_name=None
        )
        
        # 메타데이터 추가
        all_articles = []
        for article in sasb_only_articles:
            article_dict = article.dict() if hasattr(article, 'dict') else dict(article)
            article_dict['search_type'] = 'sasb_only'
            all_articles.append(article_dict)
        
        logger.info(f"SASB 전용 검색 완료: {len(all_articles)}개 기사")
        return all_articles
    
    @staticmethod
    async def _analyze_and_cache_news(analysis_service, keywords: List[str], company_name: Optional[str]):
        """뉴스 분석 및 캐시 (실제 구현은 서비스별로 다름)"""
        # 이 함수는 원본 async_analyze_and_cache_news 함수를 참조해야 함
        # 실제 구현에서는 import로 가져와서 사용
        # 임시로 빈 리스트 반환 (실제 구현 시 교체 필요)
        return []
    
    @staticmethod
    def merge_and_deduplicate_articles(
        existing_articles: List[Dict[str, Any]], 
        new_articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """기사 병합 및 중복 제거"""
        combined_articles = existing_articles + new_articles
        seen_links: Set[str] = set()
        unique_articles = []
        
        for article in combined_articles:
            link = article.get('link', '')
            if link and link not in seen_links:
                seen_links.add(link)
                unique_articles.append(article)
        
        logger.info(f"중복 제거 완료: {len(combined_articles)}개 → {len(unique_articles)}개")
        return unique_articles
    
    @staticmethod
    def update_keyword_index(redis_client, index_redis_key: str, current_index: int, keyword_list: List[str]):
        """다음 키워드 인덱스로 업데이트"""
        next_index = (current_index + 1) % len(keyword_list)
        redis_client.set(index_redis_key, str(next_index))
        logger.info(f"키워드 인덱스 업데이트: {current_index} → {next_index}")

class CacheManager:
    """Redis 캐시 관리 헬퍼 클래스"""
    
    @staticmethod
    def get_existing_articles(redis_client, result_redis_key: str) -> List[Dict[str, Any]]:
        """기존 캐시된 기사들 조회"""
        try:
            existing_data_str = redis_client.get(result_redis_key)
            existing_articles = json.loads(existing_data_str) if existing_data_str else []
            logger.info(f"기존 캐시된 기사: {len(existing_articles)}개")
            return existing_articles
        except Exception as e:
            logger.error(f"기존 기사 조회 실패: {e}")
            return []
    
    @staticmethod
    def save_articles_to_cache(
        redis_client, 
        result_redis_key: str, 
        articles: List[Dict[str, Any]], 
        max_articles: int = 100,
        expire_seconds: int = 3600
    ) -> int:
        """기사들을 Redis에 캐시"""
        try:
            # 최대 개수 제한
            if len(articles) > max_articles:
                articles = articles[:max_articles]
            
            # Redis에 저장
            redis_client.set(
                result_redis_key, 
                json.dumps(articles, ensure_ascii=False), 
                ex=expire_seconds
            )
            
            logger.info(f"Redis에 {len(articles)}개 기사 캐시 완료")
            return len(articles)
            
        except Exception as e:
            logger.error(f"Redis 캐시 저장 실패: {e}")
            return 0
    
    @staticmethod
    def update_status(redis_client, status_redis_key: str, status: str):
        """작업 상태 업데이트"""
        try:
            redis_client.set(status_redis_key, status)
            logger.info(f"상태 업데이트: {status}")
        except Exception as e:
            logger.error(f"상태 업데이트 실패: {e}")

class AsyncWorkflowManager:
    """비동기 워크플로우 관리 클래스"""
    
    @staticmethod
    def create_safe_event_loop():
        """Celery 워커에서 안전한 이벤트 루프 생성"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("새 이벤트 루프 생성 완료")
            return loop
        except Exception as e:
            logger.error(f"이벤트 루프 생성 실패: {e}")
            raise
    
    @staticmethod
    def close_event_loop(loop):
        """이벤트 루프 안전하게 종료"""
        try:
            if loop and not loop.is_closed():
                loop.close()
                logger.info("이벤트 루프 종료 완료")
        except Exception as e:
            logger.error(f"이벤트 루프 종료 실패: {e}")
    
    @staticmethod
    async def run_dual_search_workflow(
        analysis_service,
        keyword: str,
        companies: Optional[List[str]],
        search_type: str
    ) -> List[Dict[str, Any]]:
        """이중 검색 워크플로우 실행"""
        all_new_articles = []
        
        try:
            # 회사 + SASB 검색
            if search_type in ["company_sasb", "dual"] and companies:
                company_articles = await DualSearchHelper.execute_company_sasb_search(
                    analysis_service, keyword, companies
                )
                all_new_articles.extend(company_articles)
            
            # SASB 전용 검색  
            if search_type in ["sasb_only", "dual"]:
                sasb_articles = await DualSearchHelper.execute_sasb_only_search(
                    analysis_service, keyword
                )
                all_new_articles.extend(sasb_articles)
            
            logger.info(f"이중 검색 워크플로우 완료: 총 {len(all_new_articles)}개 기사")
            return all_new_articles
            
        except Exception as e:
            logger.error(f"이중 검색 워크플로우 실패: {e}")
            raise 