"""
뉴스 검색 헬퍼 모듈
SASB 서비스와 Material 서비스에서 공통으로 사용하는 뉴스 검색 로직
"""
import random
import logging
from typing import List, Optional, Set, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class NewsSearchHelper:
    """뉴스 검색 관련 공통 헬퍼 클래스"""
    
    @staticmethod
    def sample_keywords(
        domain_keywords: List[str], 
        issue_keywords: List[str],
        max_domain: int = 3,
        max_issues: int = 5
    ) -> Tuple[List[str], List[str]]:
        """
        키워드 리스트에서 랜덤 샘플링
        
        Args:
            domain_keywords: 산업/도메인 키워드 리스트
            issue_keywords: 이슈 키워드 리스트  
            max_domain: 최대 도메인 키워드 수
            max_issues: 최대 이슈 키워드 수
            
        Returns:
            (샘플링된 도메인 키워드, 샘플링된 이슈 키워드)
        """
        sampled_domain = random.sample(
            domain_keywords, 
            min(max_domain, len(domain_keywords))
        )
        sampled_issues = random.sample(
            issue_keywords, 
            min(max_issues, len(issue_keywords))
        )
        
        logger.debug(f"키워드 샘플링 완료: 도메인 {len(sampled_domain)}개, 이슈 {len(sampled_issues)}개")
        return sampled_domain, sampled_issues
    
    @staticmethod
    def generate_search_queries(
        domain_keywords: List[str],
        issue_keywords: List[str],
        company_name: Optional[str] = None,
        max_combinations: int = 5
    ) -> List[str]:
        """
        검색 쿼리 조합 생성
        
        Args:
            domain_keywords: 도메인 키워드 리스트
            issue_keywords: 이슈 키워드 리스트
            company_name: 회사명 (선택적)
            max_combinations: 최대 조합 수
            
        Returns:
            생성된 검색 쿼리 리스트
        """
        queries = []
        combinations_created = 0
        
        for domain_keyword in domain_keywords:
            for issue_keyword in issue_keywords:
                if combinations_created >= max_combinations:
                    break
                    
                # 쿼리 조합 생성
                if company_name:
                    query = f"{company_name} {domain_keyword} {issue_keyword}"
                else:
                    query = f"{domain_keyword} {issue_keyword}"
                
                queries.append(query)
                combinations_created += 1
            
            if combinations_created >= max_combinations:
                break
        
        logger.info(f"검색 쿼리 {len(queries)}개 생성 완료")
        return queries
    
    @staticmethod
    def deduplicate_news_items(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        뉴스 기사 중복 제거 (링크 기준)
        
        Args:
            news_items: 뉴스 기사 리스트
            
        Returns:
            중복 제거된 뉴스 기사 리스트
        """
        seen_links: Set[str] = set()
        unique_items = []
        
        for item in news_items:
            link = item.get('link', '')
            if link and link not in seen_links:
                seen_links.add(link)
                unique_items.append(item)
        
        logger.info(f"중복 제거 완료: {len(news_items)}개 → {len(unique_items)}개")
        return unique_items
    
    @staticmethod
    def create_search_query_combinations(
        keywords_groups: List[List[str]],
        max_combinations: int = 10,
        separator: str = " "
    ) -> List[str]:
        """
        여러 키워드 그룹의 조합으로 검색 쿼리 생성
        
        Args:
            keywords_groups: 키워드 그룹들의 리스트 (예: [[회사명], [도메인키워드], [이슈키워드]])
            max_combinations: 최대 조합 수
            separator: 키워드 구분자
            
        Returns:
            조합된 검색 쿼리 리스트
        """
        import itertools
        
        # 모든 조합 생성
        all_combinations = list(itertools.product(*keywords_groups))
        
        # 최대 조합 수 제한
        if len(all_combinations) > max_combinations:
            all_combinations = random.sample(all_combinations, max_combinations)
        
        # 쿼리 문자열 생성
        queries = [separator.join(combination) for combination in all_combinations]
        
        logger.info(f"조합 쿼리 {len(queries)}개 생성")
        return queries
    
    @staticmethod
    def filter_news_by_relevance(
        news_items: List[Dict[str, Any]], 
        required_keywords: List[str],
        min_keyword_matches: int = 1
    ) -> List[Dict[str, Any]]:
        """
        관련성 기준으로 뉴스 필터링
        
        Args:
            news_items: 뉴스 기사 리스트
            required_keywords: 필수 키워드 리스트
            min_keyword_matches: 최소 키워드 매칭 수
            
        Returns:
            필터링된 뉴스 기사 리스트
        """
        filtered_items = []
        
        for item in news_items:
            title = item.get('title', '').lower()
            description = item.get('description', '').lower()
            full_text = f"{title} {description}"
            
            # 키워드 매칭 카운트
            matches = sum(1 for keyword in required_keywords 
                         if keyword.lower() in full_text)
            
            if matches >= min_keyword_matches:
                item['keyword_matches'] = matches
                filtered_items.append(item)
        
        # 키워드 매칭 수로 정렬 (높은 순)
        filtered_items.sort(key=lambda x: x.get('keyword_matches', 0), reverse=True)
        
        logger.info(f"관련성 필터링 완료: {len(news_items)}개 → {len(filtered_items)}개")
        return filtered_items

class NewsAnalysisHelper:
    """뉴스 분석 관련 헬퍼 클래스"""
    
    @staticmethod
    def calculate_news_stats(news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """뉴스 기사 통계 계산"""
        if not news_items:
            return {
                "total_count": 0,
                "sentiment_distribution": {},
                "average_length": 0
            }
        
        # 감정 분포 계산
        sentiment_counts = {}
        total_length = 0
        
        for item in news_items:
            sentiment = item.get('sentiment', '중립')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            title_len = len(item.get('title', ''))
            desc_len = len(item.get('description', ''))
            total_length += title_len + desc_len
        
        return {
            "total_count": len(news_items),
            "sentiment_distribution": sentiment_counts,
            "average_length": total_length // len(news_items) if news_items else 0
        }
    
    @staticmethod
    def extract_keywords_from_news(
        news_items: List[Dict[str, Any]], 
        min_frequency: int = 2
    ) -> List[str]:
        """뉴스에서 자주 등장하는 키워드 추출"""
        import re
        from collections import Counter
        
        # 모든 텍스트 수집
        all_text = []
        for item in news_items:
            title = item.get('title', '')
            description = item.get('description', '')
            all_text.append(f"{title} {description}")
        
        # 한국어 키워드 추출 (간단한 정규식 사용)
        combined_text = ' '.join(all_text)
        keywords = re.findall(r'[가-힣]{2,}', combined_text)
        
        # 빈도 계산 및 필터링
        keyword_counts = Counter(keywords)
        frequent_keywords = [
            keyword for keyword, count in keyword_counts.items() 
            if count >= min_frequency
        ]
        
        return frequent_keywords[:20]  # 상위 20개만 반환 