from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IndustryAnalysisService:
    """산업별 중대성 이슈 분석 서비스 (MVP: 신재생에너지 전용)
    
    신재생에너지 산업의 중대성 이슈들을 분석:
    - 두산퓨얼셀, LS ELECTRIC 관련 뉴스 분석
    - 신재생에너지 산업 주요 SASB 이슈 식별
    - 이슈별 중요도 및 트렌드 분석
    
    주의: 산업 분석 결과는 참고용입니다.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # MVP: 신재생에너지 산업만 지원
        self.supported_industries = {
            "신재생에너지": {
                "description": "태양광, 풍력, 연료전지 등 신재생에너지 산업",
                "key_sasb_topics": ["기후변화 대응", "환경 영향", "에너지 효율", "기술 혁신", "안전", "규제 준수"],
                "related_companies": ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"]
            }
        }
    
    def get_supported_industries(self) -> List[str]:
        """지원 산업 목록 반환 (MVP: 신재생에너지만)"""
        return list(self.supported_industries.keys())
    
    def get_industry_info(self, industry: str) -> Dict[str, Any]:
        """산업 정보 반환"""
        return self.supported_industries.get(industry, {})
    
    async def analyze_industry_materiality(
        self,
        industry: str,
        year: int,
        max_articles: int = 100,
        include_sasb_mapping: bool = True
    ) -> Dict[str, Any]:
        """신재생에너지 산업 중대성 이슈 분석
        
        Args:
            industry: 산업명 (신재생에너지만 지원)
            year: 분석 연도
            max_articles: 분석할 최대 뉴스 수
            include_sasb_mapping: SASB 매핑 포함 여부
            
        Returns:
            Dict[str, Any]: 신재생에너지 산업 중대성 이슈 분석 결과
        """
        self.logger.info(f"🏭 {industry} 산업 중대성 이슈 분석 시작")
        
        # MVP: 신재생에너지만 지원
        if industry != "신재생에너지":
            return {
                "analysis_metadata": {
                    "industry": industry,
                    "analysis_year": year,
                    "analysis_date": datetime.now().isoformat(),
                    "error": "unsupported_industry"
                },
                "error": "unsupported_industry",
                "message": f"MVP 단계에서는 신재생에너지 산업만 지원합니다. 지원 산업: {', '.join(self.get_supported_industries())}"
            }
        
        try:
            # 1. 산업 정보 로드
            industry_info = self.get_industry_info(industry)
            
            # 2. 두산퓨얼셀, LS ELECTRIC 뉴스 데이터 수집
            news_data = await self._collect_renewable_energy_news(year, max_articles)
            
            # 3. 신재생에너지 주요 이슈 분석
            issue_analysis = await self._analyze_renewable_energy_issues(
                news_data, industry_info, include_sasb_mapping
            )
            
            # 4. 간단한 트렌드 분석
            trend_analysis = await self._analyze_renewable_energy_trends(news_data)
            
            # 5. 결과 종합
            return {
                "analysis_metadata": {
                    "industry": industry,
                    "analysis_year": year,
                    "analysis_date": datetime.now().isoformat(),
                    "analysis_type": "renewable_energy_industry_analysis",
                    "disclaimer": "신재생에너지 산업 분석 결과는 참고용입니다."
                },
                "industry_info": industry_info,
                "news_data_summary": {
                    "total_articles_analyzed": len(news_data.get('articles', [])),
                    "companies_analyzed": ["두산퓨얼셀", "LS ELECTRIC"],
                    "analysis_period": f"{year}년"
                },
                "materiality_analysis": {
                    "key_issues": issue_analysis.get('key_issues', []),
                    "emerging_issues": issue_analysis.get('emerging_issues', []),
                    "sasb_mapping": issue_analysis.get('sasb_mapping', {}) if include_sasb_mapping else None
                },
                "trend_analysis": trend_analysis,
                "recommendations": self._generate_renewable_energy_recommendations(
                    issue_analysis, trend_analysis
                )
            }
            
        except Exception as e:
            self.logger.error(f"신재생에너지 산업 분석 실패: {str(e)}")
            return {
                "analysis_metadata": {
                    "industry": industry,
                    "analysis_year": year,
                    "analysis_date": datetime.now().isoformat(),
                    "error": str(e)
                },
                "error": "analysis_failed",
                "message": f"신재생에너지 산업 분석 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def _collect_renewable_energy_news(
        self,
        year: int,
        max_articles: int
    ) -> Dict[str, Any]:
        """두산퓨얼셀, LS ELECTRIC 뉴스 데이터 수집"""
        try:
            # Gateway 클라이언트를 통해 뉴스 데이터 수집
            from ...core.gateway_client import GatewayClient
            gateway_client = GatewayClient()
            
            # 두 회사 뉴스 수집
            companies = ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"]
            all_articles = []
            
            for company in companies:
                try:
                    news_result = await gateway_client.search_news_by_keywords(
                        keywords=[company],
                        date_range={"start": f"{year}-01-01", "end": f"{year}-12-31"},
                        limit=max_articles // 2
                    )
                    
                    if news_result.get("success") and news_result.get("data"):
                        articles = news_result["data"]
                        all_articles.extend(articles)
                except Exception as e:
                    self.logger.warning(f"'{company}' 뉴스 수집 실패: {str(e)}")
                    continue
            
            return {
                "articles": all_articles[:max_articles],
                "metadata": {
                    "period": f"{year}년",
                    "sources": ["sasb-service"],
                    "companies": companies
                }
            }
            
        except Exception as e:
            self.logger.error(f"신재생에너지 뉴스 데이터 수집 실패: {str(e)}")
            return {
                "articles": [],
                "metadata": {
                    "period": f"{year}년",
                    "sources": [],
                    "error": str(e)
                }
            }
    
    async def _analyze_renewable_energy_issues(
        self,
        news_data: Dict[str, Any],
        industry_info: Dict[str, Any],
        include_sasb_mapping: bool
    ) -> Dict[str, Any]:
        """신재생에너지 주요 이슈 분석"""
        articles = news_data.get('articles', [])
        
        if not articles:
            return {
                "key_issues": [],
                "emerging_issues": [],
                "sasb_mapping": {}
            }
        
        # 신재생에너지 주요 SASB 토픽
        key_sasb_topics = industry_info.get('key_sasb_topics', [])
        
        # 간단한 키워드 기반 이슈 분석
        topic_mentions = {}
        for topic in key_sasb_topics:
            count = 0
            for article in articles:
                title = article.get('title', '').lower()
                content = article.get('content', '').lower()
                
                # 토픽별 키워드 매칭
                if any(keyword in title + content for keyword in self._get_renewable_energy_keywords(topic)):
                    count += 1
            
            topic_mentions[topic] = count
        
        # 상위 이슈 식별
        sorted_topics = sorted(topic_mentions.items(), key=lambda x: x[1], reverse=True)
        
        key_issues = []
        for topic, count in sorted_topics:
            if count > 0:
                key_issues.append({
                    "issue_name": topic,
                    "mention_count": count,
                    "relevance_score": min(count / len(articles), 1.0),
                    "sasb_category": topic
                })
        
        # 신흥 이슈 (적은 언급이지만 존재)
        emerging_issues = []
        for topic, count in sorted_topics:
            if 0 < count < 3:
                emerging_issues.append({
                    "issue_name": topic,
                    "mention_count": count,
                    "trend": "emerging"
                })
        
        return {
            "key_issues": key_issues,
            "emerging_issues": emerging_issues,
            "sasb_mapping": topic_mentions if include_sasb_mapping else {}
        }
    
    def _get_renewable_energy_keywords(self, topic: str) -> List[str]:
        """신재생에너지 토픽별 키워드 반환"""
        keyword_map = {
            "기후변화 대응": ["기후변화", "탄소중립", "온실가스", "탄소배출", "넷제로"],
            "환경 영향": ["환경", "오염", "친환경", "생태계", "환경보호"],
            "에너지 효율": ["에너지효율", "효율성", "절약", "최적화"],
            "기술 혁신": ["기술", "혁신", "R&D", "개발", "특허", "연구"],
            "안전": ["안전", "사고", "위험", "보안", "안전성"],
            "규제 준수": ["규제", "법규", "정책", "제도", "컴플라이언스"]
        }
        
        return keyword_map.get(topic, [topic])
    
    async def _analyze_renewable_energy_trends(
        self,
        news_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """신재생에너지 트렌드 분석"""
        articles = news_data.get('articles', [])
        
        if not articles:
            return {
                "overall_trend": "insufficient_data",
                "key_trends": []
            }
        
        # 간단한 트렌드 분석
        key_trends = []
        
        # 수소 에너지 트렌드
        hydrogen_count = sum(1 for article in articles 
                           if any(keyword in article.get('title', '').lower() + article.get('content', '').lower() 
                                 for keyword in ['수소', '연료전지', '수소에너지']))
        
        if hydrogen_count > 0:
            key_trends.append({
                "trend_name": "수소 에너지 확산",
                "mention_count": hydrogen_count,
                "trend_direction": "increasing",
                "impact_level": "high" if hydrogen_count > len(articles) * 0.3 else "medium"
            })
        
        # 에너지 저장 시스템 (ESS) 트렌드
        ess_count = sum(1 for article in articles 
                       if any(keyword in article.get('title', '').lower() + article.get('content', '').lower() 
                             for keyword in ['ess', '에너지저장', '배터리', '저장시스템']))
        
        if ess_count > 0:
            key_trends.append({
                "trend_name": "에너지 저장 시스템 확산",
                "mention_count": ess_count,
                "trend_direction": "increasing",
                "impact_level": "high" if ess_count > len(articles) * 0.2 else "medium"
            })
        
        return {
            "overall_trend": "positive" if key_trends else "neutral",
            "key_trends": key_trends,
            "analysis_confidence": "medium"
        }
    
    def _generate_renewable_energy_recommendations(
        self,
        issue_analysis: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> List[str]:
        """신재생에너지 산업 추천 사항 생성"""
        recommendations = []
        
        # 기본 추천사항
        recommendations.append("신재생에너지 산업의 주요 중대성 이슈들에 대한 지속적인 모니터링이 필요합니다.")
        
        # 주요 이슈 기반 추천
        key_issues = issue_analysis.get('key_issues', [])
        if key_issues:
            top_issue = key_issues[0]['issue_name']
            recommendations.append(f"'{top_issue}' 이슈에 대한 우선적인 관리가 필요합니다.")
        
        # 트렌드 기반 추천
        key_trends = trend_analysis.get('key_trends', [])
        for trend in key_trends:
            if trend['trend_direction'] == 'increasing':
                recommendations.append(f"'{trend['trend_name']}' 트렌드에 대한 대응 전략이 필요합니다.")
        
        # 신흥 이슈 기반 추천
        emerging_issues = issue_analysis.get('emerging_issues', [])
        if emerging_issues:
            recommendations.append("신흥 이슈들에 대한 선제적 대응이 필요합니다.")
        
        return recommendations 