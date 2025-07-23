from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from collections import defaultdict
import math

from ..model.materiality_dto import (
    MaterialityTopic, MaterialityAssessment, MaterialityHistory,
    MaterialityTrendAnalysis, IssueChangeType, MaterialityUpdateRecommendation
)
from .news_analysis_engine import NewsAnalysisEngine
from .materiality_mapping_service import MaterialityMappingService
from ...core.gateway_client import GatewayClient

logger = logging.getLogger(__name__)

class MaterialityUpdateEngine:
    """중대성 평가 업데이트 엔진
    
    전년도 중대성 평가와 당년 뉴스 분석 결과를 비교하여:
    - 변화 추세 분석
    - 우선순위 변동 감지
    - 신규 이슈 발굴
    - 업데이트 필요성 판단
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.news_engine = NewsAnalysisEngine()
        self.mapping_service = MaterialityMappingService()
        self.gateway_client = GatewayClient()
        
        # 변화 감지 임계값 설정
        self.thresholds = {
            'significant_change': 0.3,      # 중요한 변화 임계값
            'emerging_issue': 0.5,          # 부상 이슈 임계값
            'declining_issue': 0.2,         # 쇠퇴 이슈 임계값
            'new_issue_score': 0.4,         # 신규 이슈 점수 임계값
            'priority_change': 2            # 우선순위 변화 임계값
        }
    
    async def analyze_materiality_evolution(
        self,
        previous_assessment: MaterialityAssessment,
        current_year: int,
        company_name: str
    ) -> Dict[str, Any]:
        """중대성 평가 변화 분석
        
        Args:
            previous_assessment: 전년도 중대성 평가
            current_year: 당년도
            company_name: 기업명
            
        Returns:
            Dict[str, Any]: 변화 분석 결과
        """
        self.logger.info(f"🔄 중대성 평가 변화 분석 시작: {company_name} {current_year}")
        
        # 1. 현재 연도 뉴스 데이터 수집
        current_news_data = await self._collect_current_news_data(company_name, current_year)
        
        # 2. 뉴스 데이터 분석
        news_analysis_results = self.news_engine.analyze_news_for_materiality(
            current_news_data['articles'],
            previous_assessment.topics,
            company_name
        )
        
        # 3. 토픽별 변화 분석
        topic_changes = self._analyze_topic_changes(
            previous_assessment.topics,
            news_analysis_results
        )
        
        # 4. 신규 이슈 발굴
        new_issues = await self._discover_new_issues(
            current_news_data['articles'],
            previous_assessment.topics,
            company_name
        )
        
        # 5. 전체 변화 트렌드 분석
        overall_trend = self._analyze_overall_trend(
            topic_changes,
            new_issues,
            current_news_data['metadata']
        )
        
        # 6. 업데이트 우선순위 계산
        update_priorities = self._calculate_update_priorities(
            topic_changes,
            new_issues,
            overall_trend
        )
        
        evolution_analysis = {
            'analysis_date': datetime.now().isoformat(),
            'company_name': company_name,
            'previous_year': previous_assessment.year,
            'current_year': current_year,
            'news_data_summary': {
                'total_articles': len(current_news_data['articles']),
                'analysis_period': current_news_data['metadata']['period'],
                'data_sources': current_news_data['metadata']['sources']
            },
            'topic_changes': topic_changes,
            'new_issues': new_issues,
            'overall_trend': overall_trend,
            'update_priorities': update_priorities,
            'recommendations': self._generate_update_recommendations(
                topic_changes, new_issues, overall_trend
            )
        }
        
        self.logger.info(f"✅ 중대성 평가 변화 분석 완료: {len(topic_changes)}개 토픽 분석")
        return evolution_analysis
    
    async def _collect_current_news_data(
        self,
        company_name: str,
        year: int
    ) -> Dict[str, Any]:
        """현재 연도 뉴스 데이터 수집"""
        try:
            # 1. sasb-service에서 기업 관련 뉴스 수집
            date_range = {
                'start_date': f"{year}-01-01",
                'end_date': f"{year}-12-31"
            }
            
            # 기업명 + SASB 키워드로 검색
            sasb_keywords = self.mapping_service.get_sasb_issue_keywords()
            company_keywords = [company_name] + sasb_keywords[:10]  # 상위 10개 SASB 키워드
            
            news_result = await self.gateway_client.search_news_by_keywords(
                keywords=company_keywords,
                date_range=date_range,
                limit=500
            )
            
            articles = news_result.get('results', [])
            
            return {
                'articles': articles,
                'metadata': {
                    'period': f"{year}-01-01 ~ {year}-12-31",
                    'sources': ['sasb-service'],
                    'search_keywords': company_keywords,
                    'total_found': len(articles)
                }
            }
            
        except Exception as e:
            self.logger.error(f"뉴스 데이터 수집 실패: {str(e)}")
            return {
                'articles': [],
                'metadata': {
                    'period': f"{year}-01-01 ~ {year}-12-31",
                    'sources': [],
                    'search_keywords': [],
                    'total_found': 0,
                    'error': str(e)
                }
            }
    
    def _analyze_topic_changes(
        self,
        previous_topics: List[MaterialityTopic],
        news_analysis_results: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """토픽별 변화 분석 (언급 수 기반 우선순위 적용)"""
        topic_changes = []
        
        # 1. 언급 수 기반 현재 순위 계산
        mention_rankings = self._calculate_mention_rankings(previous_topics, news_analysis_results)
        
        for topic in previous_topics:
            topic_name = topic.topic_name
            previous_priority = topic.priority
            
            # 뉴스 분석 결과에서 해당 토픽의 현재 상태 확인
            current_analysis = news_analysis_results.get(topic_name, {})
            current_mention_ranking = mention_rankings.get(topic_name, {})
            
            if not current_analysis:
                # 뉴스에서 관련 내용을 찾지 못한 경우
                change_analysis = {
                    'topic_name': topic_name,
                    'previous_priority': previous_priority,
                    'current_priority': len(previous_topics),  # 최하위 순위로 설정
                    'current_score': 0.0,
                    'mention_count': 0,
                    'mention_ranking': len(previous_topics),
                    'change_type': IssueChangeType.DECLINING.value,
                    'change_magnitude': -1.0,
                    'priority_shift': len(previous_topics) - previous_priority,
                    'trend_direction': 'declining',
                    'confidence': 0.3,
                    'reasons': ['뉴스에서 관련 내용 부족'],
                    'news_metrics': {
                        'total_articles': 0,
                        'relevant_articles': 0,
                        'avg_sentiment': 'neutral'
                    }
                }
            else:
                # 🎯 언급 수 기반 우선순위 계산
                mention_count = current_analysis.get('relevant_news_count', 0)
                current_priority = current_mention_ranking.get('rank', previous_priority)
                priority_shift = current_priority - previous_priority
                
                # 뉴스 분석 결과 기반 변화 분석
                current_score = current_analysis['comprehensive_score']
                change_magnitude = self._calculate_change_magnitude(
                    previous_priority, current_score
                )
                
                # 🎯 우선순위 변화와 언급 수를 고려한 변화 유형 결정
                change_type = self._determine_change_type_with_priority(
                    previous_priority, current_priority, mention_count, change_magnitude
                )
                
                confidence = self._calculate_confidence_score(current_analysis)
                
                change_analysis = {
                    'topic_name': topic_name,
                    'previous_priority': previous_priority,
                    'current_priority': current_priority,
                    'current_score': current_score,
                    'mention_count': mention_count,
                    'mention_ranking': current_priority,
                    'priority_shift': priority_shift,
                    'change_type': change_type,
                    'change_magnitude': change_magnitude,
                    'trend_direction': current_analysis['trend_analysis']['trend_direction'],
                    'confidence': confidence,
                    'reasons': self._generate_change_reasons_with_priority(
                        change_type, current_analysis, change_magnitude, priority_shift, mention_count
                    ),
                    'news_metrics': {
                        'total_articles': current_analysis['total_news_count'],
                        'relevant_articles': current_analysis['relevant_news_count'],
                        'avg_sentiment': current_analysis['trend_analysis']['avg_sentiment']
                    },
                    'detailed_analysis': current_analysis,
                    'priority_analysis': {
                        'previous_rank': previous_priority,
                        'current_rank': current_priority,
                        'rank_change': priority_shift,
                        'mention_based_rank': current_priority,
                        'rank_change_reason': self._explain_priority_shift(priority_shift, mention_count)
                    }
                }
            
            topic_changes.append(change_analysis)
        
        return topic_changes
    
    def _calculate_mention_rankings(
        self,
        topics: List[MaterialityTopic],
        news_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """🎯 언급 수 기반 토픽 순위 계산"""
        mention_counts = []
        
        # 각 토픽의 언급 수 수집
        for topic in topics:
            topic_name = topic.topic_name
            analysis = news_results.get(topic_name, {})
            mention_count = analysis.get('relevant_news_count', 0)
            
            mention_counts.append({
                'topic_name': topic_name,
                'mention_count': mention_count,
                'previous_priority': topic.priority
            })
        
        # 언급 수 기준으로 정렬 (내림차순)
        mention_counts.sort(key=lambda x: x['mention_count'], reverse=True)
        
        # 순위 매기기
        rankings = {}
        for i, item in enumerate(mention_counts):
            rankings[item['topic_name']] = {
                'rank': i + 1,
                'mention_count': item['mention_count'],
                'previous_rank': item['previous_priority']
            }
        
        self.logger.info(f"🎯 언급 수 기반 순위 계산 완료: {len(rankings)}개 토픽")
        return rankings
    
    def _determine_change_type_with_priority(
        self,
        previous_priority: int,
        current_priority: int,
        mention_count: int,
        change_magnitude: float
    ) -> str:
        """🎯 우선순위 변화를 고려한 변화 유형 결정"""
        priority_shift = current_priority - previous_priority
        
        # 순위가 상승한 경우 (숫자가 작아짐)
        if priority_shift < -1:  # 2단계 이상 상승
            if mention_count >= 5:
                return IssueChangeType.SIGNIFICANT_INCREASE.value
            else:
                return IssueChangeType.EMERGING.value
        
        # 순위가 하락한 경우 (숫자가 커짐)
        elif priority_shift > 1:  # 2단계 이상 하락
            if mention_count <= 2:
                return IssueChangeType.DECLINING.value
            else:
                return IssueChangeType.MODERATE_DECREASE.value
        
        # 순위 변화가 적은 경우
        else:
            if change_magnitude > self.thresholds['significant_change']:
                return IssueChangeType.MODERATE_INCREASE.value
            elif change_magnitude < -self.thresholds['significant_change']:
                return IssueChangeType.MODERATE_DECREASE.value
            else:
                return IssueChangeType.STABLE.value
    
    def _generate_change_reasons_with_priority(
        self,
        change_type: str,
        analysis: Dict[str, Any],
        change_magnitude: float,
        priority_shift: int,
        mention_count: int
    ) -> List[str]:
        """🎯 우선순위 변화를 포함한 변화 이유 생성"""
        reasons = []
        
        # 우선순위 변화 이유
        if priority_shift < -1:
            reasons.append(f"언급 수 증가로 {abs(priority_shift)}단계 순위 상승 (총 {mention_count}회 언급)")
        elif priority_shift > 1:
            reasons.append(f"언급 수 감소로 {priority_shift}단계 순위 하락 (총 {mention_count}회 언급)")
        elif priority_shift == 0:
            reasons.append(f"순위 유지 (총 {mention_count}회 언급)")
        
        # 기존 변화 이유 추가
        reasons.extend(self._generate_change_reasons(change_type, analysis, change_magnitude))
        
        return reasons
    
    def _explain_priority_shift(self, priority_shift: int, mention_count: int) -> str:
        """우선순위 변화 이유 설명"""
        if priority_shift < -1:
            return f"언급 빈도 증가 ({mention_count}회)로 인한 중요도 상승"
        elif priority_shift > 1:
            return f"언급 빈도 감소 ({mention_count}회)로 인한 중요도 하락"
        else:
            return f"언급 빈도 유지 ({mention_count}회)로 순위 안정"
    
    def _calculate_change_magnitude(
        self,
        previous_priority: int,
        current_score: float
    ) -> float:
        """변화 크기 계산"""
        # 이전 우선순위를 점수로 변환 (낮은 우선순위 = 높은 점수)
        max_priority = 10  # 가정: 최대 우선순위는 10
        previous_score = (max_priority - previous_priority + 1) / max_priority
        
        # 현재 점수와 비교
        change_magnitude = current_score - previous_score
        
        return round(change_magnitude, 3)
    
    def _determine_change_type(
        self,
        previous_priority: int,
        current_score: float,
        change_magnitude: float
    ) -> str:
        """변화 유형 결정"""
        if change_magnitude > self.thresholds['significant_change']:
            return IssueChangeType.EMERGING.value
        elif change_magnitude < -self.thresholds['significant_change']:
            return IssueChangeType.DECLINING.value
        elif current_score > self.thresholds['emerging_issue']:
            return IssueChangeType.ONGOING.value
        else:
            return IssueChangeType.MATURING.value
    
    def _calculate_confidence_score(
        self,
        analysis_result: Dict[str, Any]
    ) -> float:
        """분석 결과 신뢰도 계산"""
        news_count = analysis_result.get('total_news_count', 0)
        relevant_count = analysis_result.get('relevant_news_count', 0)
        score = analysis_result.get('comprehensive_score', 0)
        
        # 뉴스 개수 기반 신뢰도
        news_confidence = min(news_count / 10, 1.0)  # 10개 이상이면 최대 신뢰도
        
        # 관련성 비율 기반 신뢰도
        relevance_confidence = relevant_count / max(news_count, 1)
        
        # 점수 기반 신뢰도
        score_confidence = min(score / 2.0, 1.0)  # 2.0 이상이면 최대 신뢰도
        
        # 가중 평균
        overall_confidence = (
            news_confidence * 0.3 +
            relevance_confidence * 0.4 +
            score_confidence * 0.3
        )
        
        return round(overall_confidence, 3)
    
    def _generate_change_reasons(
        self,
        change_type: str,
        analysis_result: Dict[str, Any],
        change_magnitude: float
    ) -> List[str]:
        """변화 이유 생성"""
        reasons = []
        
        trend = analysis_result.get('trend_analysis', {})
        news_count = analysis_result.get('total_news_count', 0)
        sentiment = trend.get('avg_sentiment', 'neutral')
        
        if change_type == IssueChangeType.EMERGING.value:
            reasons.append(f"뉴스 관련도 점수 상승 ({change_magnitude:+.2f})")
            if trend.get('recent_increase'):
                reasons.append("최근 뉴스 증가 추세")
            if sentiment == 'positive':
                reasons.append("긍정적 뉴스 증가")
        
        elif change_type == IssueChangeType.DECLINING.value:
            reasons.append(f"뉴스 관련도 점수 하락 ({change_magnitude:+.2f})")
            if news_count < 5:
                reasons.append("관련 뉴스 부족")
            if sentiment == 'negative':
                reasons.append("부정적 뉴스 증가")
        
        elif change_type == IssueChangeType.ONGOING.value:
            reasons.append("지속적인 뉴스 노출")
            if news_count > 10:
                reasons.append("풍부한 뉴스 데이터")
        
        else:  # MATURING
            reasons.append("안정적인 이슈 상태")
            if trend.get('trend_direction') == 'stable':
                reasons.append("트렌드 안정성")
        
        return reasons
    
    async def _discover_new_issues(
        self,
        news_articles: List[Dict[str, Any]],
        existing_topics: List[MaterialityTopic],
        company_name: str
    ) -> List[Dict[str, Any]]:
        """신규 이슈 발굴 - 현재 비활성화됨"""
        # 신규 이슈 발견 기능을 비활성화하고 기존 토픽 분석에 집중
        self.logger.info("🚫 신규 이슈 발견 기능 비활성화 - 기존 토픽 중심 분석에 집중")
        return []
    
    def _calculate_new_issue_score(
        self,
        articles: List[Dict[str, Any]],
        keyword: str,
        frequency: int
    ) -> float:
        """신규 이슈 점수 계산"""
        # 1. 빈도 점수 (로그 스케일)
        frequency_score = math.log(frequency + 1) / 10
        
        # 2. 기사 개수 점수
        article_count_score = min(len(articles) / 10, 1.0)
        
        # 3. 최근성 점수
        recent_count = 0
        for article in articles:
            if self.news_engine._is_recent_news(article.get('published_at', '')):
                recent_count += 1
        recency_score = recent_count / max(len(articles), 1)
        
        # 4. sentiment 다양성 점수
        sentiments = [article.get('sentiment', 'neutral') for article in articles]
        unique_sentiments = len(set(sentiments))
        sentiment_diversity = unique_sentiments / 3  # 최대 3개 sentiment
        
        # 5. 종합 점수
        total_score = (
            frequency_score * 0.3 +
            article_count_score * 0.3 +
            recency_score * 0.2 +
            sentiment_diversity * 0.2
        )
        
        return round(total_score, 3)
    
    def _generate_discovery_rationale(
        self,
        keyword: str,
        frequency: int,
        score: float,
        articles: List[Dict[str, Any]]
    ) -> str:
        """신규 이슈 발견 근거 생성"""
        recent_articles = [
            article for article in articles
            if self.news_engine._is_recent_news(article.get('published_at', ''))
        ]
        
        rationale = f"'{keyword}' 키워드가 {frequency}회 언급되어 신규 이슈로 식별됨. "
        rationale += f"관련 기사 {len(articles)}개 중 최근 기사 {len(recent_articles)}개. "
        rationale += f"이슈 점수: {score:.3f}"
        
        return rationale
    
    def _analyze_overall_trend(
        self,
        topic_changes: List[Dict[str, Any]],
        new_issues: List[Dict[str, Any]],
        news_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """전체 변화 트렌드 분석"""
        
        # 1. 변화 유형별 분포
        change_distribution = defaultdict(int)
        for change in topic_changes:
            change_distribution[change['change_type']] += 1
        
        # 2. 전체 변화 강도
        change_magnitudes = [abs(change['change_magnitude']) for change in topic_changes]
        avg_change_magnitude = sum(change_magnitudes) / len(change_magnitudes) if change_magnitudes else 0
        
        # 3. 신뢰도 평균
        confidences = [change['confidence'] for change in topic_changes]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # 4. 전체 트렌드 방향 결정
        emerging_count = change_distribution[IssueChangeType.EMERGING.value]
        declining_count = change_distribution[IssueChangeType.DECLINING.value]
        
        if emerging_count > declining_count:
            overall_direction = 'expanding'
        elif declining_count > emerging_count:
            overall_direction = 'contracting'
        else:
            overall_direction = 'stable'
        
        # 5. 업데이트 필요성 평가
        update_necessity = self._assess_update_necessity(
            change_distribution, avg_change_magnitude, len(new_issues)
        )
        
        return {
            'overall_direction': overall_direction,
            'change_distribution': dict(change_distribution),
            'avg_change_magnitude': round(avg_change_magnitude, 3),
            'avg_confidence': round(avg_confidence, 3),
            'new_issues_count': len(new_issues),
            'update_necessity': update_necessity,
            'analysis_summary': self._generate_trend_summary(
                overall_direction, change_distribution, len(new_issues)
            )
        }
    
    def _assess_update_necessity(
        self,
        change_distribution: Dict[str, int],
        avg_change_magnitude: float,
        new_issues_count: int
    ) -> str:
        """업데이트 필요성 평가"""
        emerging_count = change_distribution.get(IssueChangeType.EMERGING.value, 0)
        declining_count = change_distribution.get(IssueChangeType.DECLINING.value, 0)
        
        if (emerging_count >= 3 or new_issues_count >= 2 or 
            avg_change_magnitude > 0.5):
            return 'high'
        elif (emerging_count >= 1 or declining_count >= 2 or 
              avg_change_magnitude > 0.3):
            return 'medium'
        else:
            return 'low'
    
    def _generate_trend_summary(
        self,
        overall_direction: str,
        change_distribution: Dict[str, int],
        new_issues_count: int
    ) -> str:
        """트렌드 요약 생성"""
        summary = f"전체 트렌드: {overall_direction}. "
        
        if change_distribution:
            summary += f"변화 분포 - "
            summary += f"부상: {change_distribution.get(IssueChangeType.EMERGING.value, 0)}개, "
            summary += f"지속: {change_distribution.get(IssueChangeType.ONGOING.value, 0)}개, "
            summary += f"성숙: {change_distribution.get(IssueChangeType.MATURING.value, 0)}개, "
            summary += f"쇠퇴: {change_distribution.get(IssueChangeType.DECLINING.value, 0)}개. "
        
        if new_issues_count > 0:
            summary += f"신규 이슈 {new_issues_count}개 발견."
        
        return summary
    
    def _calculate_update_priorities(
        self,
        topic_changes: List[Dict[str, Any]],
        new_issues: List[Dict[str, Any]],
        overall_trend: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """업데이트 우선순위 계산"""
        priorities = []
        
        # 1. 기존 토픽 변화 우선순위
        for change in topic_changes:
            if change['change_type'] in [IssueChangeType.EMERGING.value, IssueChangeType.DECLINING.value]:
                priority_score = abs(change['change_magnitude']) * change['confidence']
                priorities.append({
                    'type': 'topic_change',
                    'topic_name': change['topic_name'],
                    'change_type': change['change_type'],
                    'priority_score': priority_score,
                    'rationale': f"기존 토픽 변화: {change['change_type']}"
                })
        
        # 2. 신규 이슈 우선순위
        for issue in new_issues:
            priority_score = issue['issue_score'] * issue['confidence']
            priorities.append({
                'type': 'new_issue',
                'topic_name': issue['keyword'],
                'change_type': 'new',
                'priority_score': priority_score,
                'rationale': f"신규 이슈 발견: {issue['discovery_rationale']}"
            })
        
        # 3. 우선순위 정렬
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return priorities
    
    def _generate_update_recommendations(
        self,
        topic_changes: List[Dict[str, Any]],
        new_issues: List[Dict[str, Any]],
        overall_trend: Dict[str, Any]
    ) -> List[str]:
        """업데이트 권장사항 생성"""
        recommendations = []
        
        # 1. 전체 트렌드 기반 권장사항
        if overall_trend['overall_direction'] == 'expanding':
            recommendations.append("중대성 평가 범위 확대를 고려하세요.")
        elif overall_trend['overall_direction'] == 'contracting':
            recommendations.append("중대성 평가 범위 축소 및 집중화를 고려하세요.")
        
        # 2. 신규 이슈 관련 권장사항
        if len(new_issues) > 0:
            recommendations.append(f"{len(new_issues)}개의 신규 이슈를 중대성 평가에 포함하는 것을 검토하세요.")
        
        # 3. 변화 강도 기반 권장사항
        if overall_trend['avg_change_magnitude'] > 0.4:
            recommendations.append("변화 강도가 높아 중대성 평가의 전면적인 재검토가 필요합니다.")
        
        # 4. 업데이트 필요성 기반 권장사항
        necessity = overall_trend['update_necessity']
        if necessity == 'high':
            recommendations.append("즉시 중대성 평가 업데이트를 실시하세요.")
        elif necessity == 'medium':
            recommendations.append("3개월 내 중대성 평가 업데이트를 계획하세요.")
        else:
            recommendations.append("현재 중대성 평가를 유지하되 정기적인 모니터링을 계속하세요.")
        
        return recommendations 