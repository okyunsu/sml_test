import asyncio
import json
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
from .celery_app import celery_app
from ..domain.service.analysis_service import AnalysisService
from ..domain.model.sasb_dto import NewsAnalysisRequest
from ..core.redis_client import RedisClient
from ..config.settings import settings
import logging

# =============================================================================
# 🎯 개선된 이중 키워드 검색 시스템
# 문제: 기존 단일 키워드 검색으로 인한 비관련 산업 뉴스 과다 수집 
# 해결: (산업 키워드) AND (SASB 이슈 키워드) 조합 검색
# =============================================================================

# 그룹 1: 신재생에너지 산업/분야 키워드 (Domain Keywords)
# 이 키워드가 포함되어야만 신재생에너지 산업 뉴스로 간주
RENEWABLE_DOMAIN_KEYWORDS = [
    # 핵심 에너지 분야
    "신재생에너지", "재생에너지", "신에너지", "청정에너지", "친환경에너지",
    
    # 발전 기술별
    "태양광", "태양열", "풍력", "수력", "수력발전", "조력", "지열", "바이오에너지", 
    "바이오매스", "바이오가스", "연료전지",
    
    # 에너지 저장 및 인프라
    "ESS", "에너지저장장치", "배터리", "수소", "그린수소", "블루수소", "암모니아",
    
    # 전력 산업
    "발전소", "발전사", "발전공기업", "전력", "전력공사", "한전", "전력거래소", 
    "송전", "배전", "전력망", "스마트그리드", "마이크로그리드",
    
    # 에너지 전환
    "에너지전환", "전원믹스", "전원구성", "에너지믹스", "RE100", "K-RE100",
    
    # 관련 기업/기관
    "에너지공사", "발전회사", "전력회사", "에너지기업", "전력산업"
]

# 그룹 2: SASB 이슈 키워드 (Issue Keywords) - 기존 53개 키워드 유지
SASB_ISSUE_KEYWORDS = [
    # 1. Greenhouse Gas Emissions & Energy Resource Planning
    "탄소중립", "탄소배출", "온실가스", "RE100", "CF100", "에너지믹스", "전원구성",
    "탄소국경세", "스코프", "감축목표", "NDC", "자발적 탄소시장",
    
    # 2. Air Quality  
    "미세먼지", "대기오염", "황산화물", "질소산화물", "바이오매스", "비산먼지",
    
    # 3. Water Management
    "수처리", "폐수", "수질오염", "냉각수", "수력발전", "그린수소", "수전해", "해양생태계",
    
    # 4. Waste & Byproduct Management
    "폐배터리", "폐패널", "폐블레이드", "자원순환", "재활용", "재사용",
    "핵심광물", "희토류", "순환경제",
    
    # 5. Energy Affordability
    "전기요금", "에너지복지", "SMP", "REC", "PPA", "그리드패리티", "에너지빈곤층",
    
    # 6. Workforce Health & Safety
    "중대재해", "산업재해", "감전사고", "추락사고", "중대재해처벌법", "안전보건",
    
    # 7. End-Use Efficiency & Demand
    "에너지효율", "수요관리", "DR", "가상발전소", "VPP", "분산에너지", "스마트그리드",
    
    # 8. Critical Incident Management
    "ESS화재", "폭발", "대규모정전", "블랙아웃", "자연재해", "댐붕괴", "안전진단",
    
    # 9. Grid Resiliency
    "전력망", "계통안정", "출력제어", "출력제한", "간헐성", "주파수", "송배전망",
    
    # 10. Ecological Impacts & Community Relations
    "입지갈등", "주민수용성", "환경영향평가", "산림훼손", "이격거리", "소음", "빛반사",
    "조류충돌", "해양생태계", "공청회", "이익공유제"
]

# 하위 호환성을 위한 기존 키워드 (deprecated, 새로운 방식 사용 권장)
RENEWABLE_KEYWORDS = SASB_ISSUE_KEYWORDS

COMPANIES = ["두산퓨얼셀", "LS ELECTRIC"]
MAX_ARTICLES_IN_CACHE = 100

# --- Helper Functions ---
def get_redis_client():
    """Helper function to create a Redis client from settings."""
    parsed_url = urlparse(settings.CELERY_BROKER_URL)
    return RedisClient(
        host=parsed_url.hostname or 'localhost',
        port=parsed_url.port or 6379,
        db=int(parsed_url.path[1:]) if parsed_url.path and parsed_url.path[1:] else 0
    )

async def async_analyze_and_cache_news(analysis_service: AnalysisService, keywords: List[str], company_name: Optional[str] = None):
    """비동기 뉴스 분석 래퍼 함수 (기존 방식)"""
    return await analysis_service.analyze_and_cache_news(keywords=keywords, company_name=company_name)

async def async_analyze_with_combined_keywords(
    analysis_service: AnalysisService, 
    domain_keywords: List[str],
    issue_keywords: List[str],
    company_name: Optional[str] = None
):
    """🎯 조합 검색을 위한 비동기 래퍼 함수 (개선된 방식)"""
    return await analysis_service.analyze_with_combined_keywords(
        domain_keywords=domain_keywords,
        issue_keywords=issue_keywords, 
        company_name=company_name,
        max_combinations=5  # API 호출 제한
    )

def run_dual_search_analysis(
    redis_client: RedisClient,
    analysis_service: AnalysisService,
    keyword_list: List[str],
    index_redis_key: str,
    result_redis_key: str,
    status_redis_key: str,
    companies: Optional[List[str]] = None,
    search_type: str = "dual"  # "company_sasb", "sasb_only", "dual"
):
    """
    새로운 이중 검색 로직: 
    1. 회사 + SASB 키워드 조합 검색
    2. SASB 키워드 전용 검색
    결과를 Redis에 캐시합니다.
    """
    redis_client.set(status_redis_key, "IN_PROGRESS")
    try:
        # 1. Get the index of the keyword to use for this run
        current_index_str = redis_client.get(index_redis_key)
        current_index = int(current_index_str) if current_index_str else 0
        
        keyword_to_search = keyword_list[current_index]
        logging.info(f"이중 검색 분석 실행: '{keyword_to_search}' (타입: {search_type})")

        # 2. Run dual search analysis using proper async handling
        all_new_articles = []
        
        # 새로운 이벤트 루프 생성 (Celery 워커에서 안전)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if search_type in ["company_sasb", "dual"] and companies:
                # 방식 1: 회사 + SASB 키워드 조합 검색
                for company in companies:
                    logging.info(f"회사+SASB 검색: {company} + {keyword_to_search}")
                    company_sasb_articles = loop.run_until_complete(
                        async_analyze_and_cache_news(
                            analysis_service,
                            keywords=[keyword_to_search], 
                            company_name=company
                        )
                    )
                    # 각 기사에 검색 타입 메타데이터 추가
                    for article in company_sasb_articles:
                        article_dict: Dict[str, Any] = article.dict()
                        article_dict['search_type'] = 'company_sasb'
                        article_dict['company'] = company
                        all_new_articles.append(article_dict)
            
            if search_type in ["sasb_only", "dual"]:
                # 방식 2: SASB 키워드 전용 검색 (회사명 없음)
                logging.info(f"SASB 전용 검색: {keyword_to_search}")
                sasb_only_articles = loop.run_until_complete(
                    async_analyze_and_cache_news(
                        analysis_service,
                        keywords=[keyword_to_search], 
                        company_name=None
                    )
                )
                # 각 기사에 검색 타입 메타데이터 추가
                for article in sasb_only_articles:
                    article_dict: Dict[str, Any] = article.dict()
                    article_dict['search_type'] = 'sasb_only'
                    all_new_articles.append(article_dict)
        
        finally:
            loop.close()

        # 3. Cache management
        existing_data_str = redis_client.get(result_redis_key)
        existing_articles = json.loads(existing_data_str) if existing_data_str else []
        
        # 4. Merge and deduplicate
        combined_articles = existing_articles + all_new_articles
        seen_links = set()
        unique_articles = []
        for article in combined_articles:
            link = article.get('link', '')
            if link and link not in seen_links:
                seen_links.add(link)
                unique_articles.append(article)
        
        # 5. Limit the number of articles and save to Redis
        if len(unique_articles) > MAX_ARTICLES_IN_CACHE:
            unique_articles = unique_articles[:MAX_ARTICLES_IN_CACHE]
        
        redis_client.set(result_redis_key, json.dumps(unique_articles, ensure_ascii=False), ex=3600)
        
        # 6. Update the index for the next run
        next_index = (current_index + 1) % len(keyword_list)
        redis_client.set(index_redis_key, str(next_index))
        
        redis_client.set(status_redis_key, "COMPLETED")
        logging.info(f"이중 검색 분석 완료. 총 {len(unique_articles)}개 기사 캐시됨.")
        
        return len(unique_articles)
    
    except Exception as e:
        logging.error(f"이중 검색 분석 중 오류 발생: {e}", exc_info=True)
        redis_client.set(status_redis_key, f"FAILED: {str(e)}")
        return 0


# --- Celery Tasks ---
@celery_app.task
def run_sasb_only_analysis():
    """Celery task for SASB-only renewable energy analysis (키워드만 사용)."""
    logging.info("실행 예약된 작업: run_sasb_only_analysis")
    try:
        redis_client = get_redis_client()
        analysis_service = AnalysisService()
        run_dual_search_analysis(
            redis_client=redis_client,
            analysis_service=analysis_service,
            keyword_list=RENEWABLE_KEYWORDS,
            index_redis_key="sasb_only_keyword_index",
            result_redis_key="latest_sasb_renewable_analysis",
            status_redis_key="status:sasb_renewable_analysis",
            companies=None,  # 회사명 없음
            search_type="sasb_only"  # SASB 키워드만 사용
        )
    except Exception as e:
        logging.error(f"run_sasb_only_analysis에서 오류 발생: {e}", exc_info=True)

@celery_app.task
def run_companies_dual_analysis():
    """
    Celery task that runs dual search analysis for each company:
    1. Company + SASB keyword combination
    2. SASB keyword only
    """
    logging.info("실행 예약된 작업: run_companies_dual_analysis (이중 검색)")
    redis_client = get_redis_client()
    analysis_service = AnalysisService()

    for company in COMPANIES:
        try:
            logging.info(f"'{company}'에 대한 이중 검색 분석 시작...")
            
            # Use company-specific Redis keys
            index_redis_key = f"company_dual_keyword_index:{company}"
            result_redis_key = f"latest_companies_renewable_analysis:{company}"
            status_redis_key = f"status:companies_renewable_analysis:{company}"

            run_dual_search_analysis(
                redis_client=redis_client,
                analysis_service=analysis_service,
                keyword_list=RENEWABLE_KEYWORDS,
                index_redis_key=index_redis_key,
                result_redis_key=result_redis_key,
                status_redis_key=status_redis_key,
                companies=[company],  # 단일 회사
                search_type="dual"  # 이중 검색: 회사+SASB + SASB만
            )
            logging.info(f"'{company}'에 대한 이중 검색 분석 완료.")
        
        except Exception as e:
            logging.error(f"'{company}'에 대한 run_companies_dual_analysis에서 오류 발생: {e}", exc_info=True)

@celery_app.task
def run_company_sasb_only_analysis():
    """
    Celery task for company + SASB keyword combination analysis only.
    """
    logging.info("실행 예약된 작업: run_company_sasb_only_analysis")
    redis_client = get_redis_client()
    analysis_service = AnalysisService()

    for company in COMPANIES:
        try:
            logging.info(f"'{company}'에 대한 회사+SASB 분석 시작...")
            
            # Use company-specific Redis keys
            index_redis_key = f"company_sasb_keyword_index:{company}"
            result_redis_key = f"latest_company_sasb_analysis:{company}"
            status_redis_key = f"status:company_sasb_analysis:{company}"

            run_dual_search_analysis(
                redis_client=redis_client,
                analysis_service=analysis_service,
                keyword_list=RENEWABLE_KEYWORDS,
                index_redis_key=index_redis_key,
                result_redis_key=result_redis_key,
                status_redis_key=status_redis_key,
                companies=[company],  # 단일 회사
                search_type="company_sasb"  # 회사+SASB 조합만
            )
            logging.info(f"'{company}'에 대한 회사+SASB 분석 완료.")
        
        except Exception as e:
            logging.error(f"'{company}'에 대한 run_company_sasb_only_analysis에서 오류 발생: {e}", exc_info=True)

@celery_app.task
def run_combined_keywords_analysis():
    """
    🎯 새로운 조합 검색 Celery 작업
    (산업 키워드) AND (SASB 이슈 키워드) 조합으로 검색
    관련성 높은 신재생에너지 산업 뉴스만 수집
    """
    logging.info("🎯 실행 예약된 작업: run_combined_keywords_analysis (조합 검색)")
    redis_client = get_redis_client()
    analysis_service = AnalysisService()
    
    try:
        # 상태 업데이트
        status_key = "status:combined_keywords_analysis"
        redis_client.set(status_key, "IN_PROGRESS")
        
        # 새로운 이벤트 루프 생성 (Celery 워커에서 안전)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 조합 검색 실행 (회사명 없이)
            logging.info("🎯 SASB 조합 검색 실행 중...")
            analyzed_articles = loop.run_until_complete(
                async_analyze_with_combined_keywords(
                    analysis_service=analysis_service,
                    domain_keywords=RENEWABLE_DOMAIN_KEYWORDS,
                    issue_keywords=SASB_ISSUE_KEYWORDS,
                    company_name=None  # 회사명 없음
                )
            )
            
            # 기사 딕셔너리로 변환 (메타데이터 추가)
            articles_with_metadata = []
            for article in analyzed_articles:
                article_dict = article.dict()
                article_dict['search_type'] = 'combined_keywords'
                article_dict['search_method'] = 'domain_and_issue_keywords'
                articles_with_metadata.append(article_dict)
            
        finally:
            loop.close()
        
        # Redis에 결과 저장
        result_key = "latest_combined_keywords_analysis"
        if articles_with_metadata:
            # 최대 100개로 제한
            limited_articles = articles_with_metadata[:MAX_ARTICLES_IN_CACHE]
            redis_client.set(
                result_key, 
                json.dumps(limited_articles, ensure_ascii=False), 
                ex=3600  # 1시간 캐시
            )
            logging.info(f"🎯 조합 검색 완료: {len(limited_articles)}개 기사 캐시됨")
        else:
            logging.warning("🎯 조합 검색 결과 없음")
            redis_client.set(result_key, json.dumps([], ensure_ascii=False), ex=1800)
        
        # 상태 완료 업데이트
        redis_client.set(status_key, "COMPLETED")
        
    except Exception as e:
        logging.error(f"🎯 run_combined_keywords_analysis에서 오류 발생: {e}", exc_info=True)
        redis_client.set("status:combined_keywords_analysis", "ERROR")

@celery_app.task 
def run_company_combined_keywords_analysis():
    """
    🎯 회사별 조합 검색 Celery 작업
    (회사명) + (산업 키워드) AND (SASB 이슈 키워드) 조합으로 검색
    """
    logging.info("🎯 실행 예약된 작업: run_company_combined_keywords_analysis (회사별 조합 검색)")
    redis_client = get_redis_client()
    analysis_service = AnalysisService()
    
    for company in COMPANIES:
        try:
            logging.info(f"🎯 '{company}'에 대한 조합 검색 시작...")
            
            # 회사별 상태 키
            status_key = f"status:company_combined_analysis:{company}"
            result_key = f"latest_company_combined_analysis:{company}"
            redis_client.set(status_key, "IN_PROGRESS")
            
            # 새로운 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 회사별 조합 검색 실행
                analyzed_articles = loop.run_until_complete(
                    async_analyze_with_combined_keywords(
                        analysis_service=analysis_service,
                        domain_keywords=RENEWABLE_DOMAIN_KEYWORDS,
                        issue_keywords=SASB_ISSUE_KEYWORDS,
                        company_name=company
                    )
                )
                
                # 기사 딕셔너리로 변환 (메타데이터 추가)
                articles_with_metadata = []
                for article in analyzed_articles:
                    article_dict = article.dict()
                    article_dict['search_type'] = 'company_combined_keywords'
                    article_dict['search_method'] = 'company_domain_and_issue_keywords'
                    article_dict['company'] = company
                    articles_with_metadata.append(article_dict)
                
            finally:
                loop.close()
            
            # Redis에 결과 저장
            if articles_with_metadata:
                limited_articles = articles_with_metadata[:MAX_ARTICLES_IN_CACHE]
                redis_client.set(
                    result_key, 
                    json.dumps(limited_articles, ensure_ascii=False), 
                    ex=3600
                )
                logging.info(f"🎯 '{company}' 조합 검색 완료: {len(limited_articles)}개 기사 캐시됨")
            else:
                logging.warning(f"🎯 '{company}' 조합 검색 결과 없음")
                redis_client.set(result_key, json.dumps([], ensure_ascii=False), ex=1800)
            
            # 상태 완료
            redis_client.set(status_key, "COMPLETED")
            
        except Exception as e:
            logging.error(f"🎯 '{company}' 조합 검색에서 오류 발생: {e}", exc_info=True)
            redis_client.set(f"status:company_combined_analysis:{company}", "ERROR") 