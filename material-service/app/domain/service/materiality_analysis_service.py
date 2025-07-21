from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from collections import defaultdict
import math

from ..model.materiality_dto import MaterialityTopic, MaterialityAssessment
from .news_analysis_engine import NewsAnalysisEngine
from .materiality_update_engine import MaterialityUpdateEngine
from .materiality_mapping_service import MaterialityMappingService
from .materiality_file_service import MaterialityFileService

logger = logging.getLogger(__name__)

class MaterialityAnalysisService:
    """중대성 평가 변화 분석 서비스
    
    뉴스 분석 결과를 바탕으로 중대성 평가 변화 가능성을 분석:
    - 우선순위 변화 가능성 제안
    - 신규 이슈 발굴 및 검토 제안
    - 기존 이슈 중요도 변화 분석
    - SASB 매핑 기반 관련성 분석
    
    주의: 뉴스 분석만으로는 확정적인 중대성 평가를 내릴 수 없으므로,
    모든 결과는 참고용 분석 및 제안 사항입니다.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.news_engine = NewsAnalysisEngine()
        self.update_engine = MaterialityUpdateEngine()
        self.mapping_service = MaterialityMappingService()
        self.file_service = MaterialityFileService()
        
        # Gateway 클라이언트 추가
        from ...core.gateway_client import GatewayClient
        self.gateway_client = GatewayClient()
        
        # 분석 파라미터 설정
        self.analysis_params = {
            'significance_threshold': 0.3,  # 중요한 변화 임계값
            'new_issue_threshold': 0.4,     # 신규 이슈 검토 임계값
            'high_confidence_threshold': 0.7,  # 높은 신뢰도 임계값
            'max_recommendations': 10       # 최대 추천 개수
        }
    
    async def check_gateway_connection(self) -> Dict[str, Any]:
        """Gateway 연결 상태 확인"""
        try:
            # Gateway 헬스체크 수행
            health_status = await self.gateway_client.get_sasb_health_check()
            return {
                "status": "connected",
                "gateway_available": True,
                "services": health_status,
                "message": "Gateway 연결 정상"
            }
        except Exception as e:
            self.logger.warning(f"Gateway 연결 확인 실패: {str(e)}")
            return {
                "status": "disconnected",
                "gateway_available": False,
                "error": str(e),
                "message": "Gateway 연결 실패 - 일부 기능이 제한될 수 있습니다"
            }
    
    async def analyze_materiality_changes(
        self,
        company_name: str,
        current_year: int,
        base_assessment: Optional[MaterialityAssessment] = None,
        include_news: bool = True,
        max_articles: int = 100
    ) -> Dict[str, Any]:
        """중대성 평가 변화 분석 및 제안 생성
        
        Args:
            company_name: 기업명
            current_year: 분석 대상 연도
            base_assessment: 기준 평가 (보통 전년도)
            include_news: 뉴스 분석 포함 여부
            max_articles: 분석할 최대 뉴스 수
            
        Returns:
            Dict[str, Any]: 분석 결과 및 제안 사항 (JSON 형태)
        """
        try:
            self.logger.info(f"🎯 {company_name} {current_year}년 중대성 평가 변화 분석 시작")
        
        # 1. 기준 평가 로드
        if base_assessment is None:
            base_assessment = self.file_service.load_company_assessment(
                company_name, current_year - 1
            )
        
        if not base_assessment:
            return await self._analyze_without_base_assessment(company_name, current_year)
        
        # 2. 변화 분석 수행
        try:
            evolution_analysis = await self.update_engine.analyze_materiality_evolution(
                base_assessment, current_year, company_name
            )
            self.logger.info(f"🔄 변화 분석 완료: {len(evolution_analysis.get('topic_changes', []))}개 토픽")
        except Exception as e:
            self.logger.error(f"❌ 변화 분석 실패: {str(e)}")
            raise
        
        # 3. 제안 사항 생성
        try:
            recommendations = self._generate_change_recommendations(
                evolution_analysis, base_assessment
            )
            self.logger.info(f"📋 제안 사항 생성 완료: {len(recommendations)}개")
        except Exception as e:
            self.logger.error(f"❌ 제안 사항 생성 실패: {str(e)}")
            raise
        
        # 4. 우선순위 변화 제안
        try:
            priority_suggestions = self._generate_priority_suggestions(
                evolution_analysis, base_assessment
            )
            self.logger.info(f"🔄 우선순위 제안 완료: {len(priority_suggestions)}개")
        except Exception as e:
            self.logger.error(f"❌ 우선순위 제안 실패: {str(e)}")
            raise
        
        # 5. 신규 이슈 검토 제안
        try:
            new_issue_suggestions = self._generate_new_issue_suggestions(
                evolution_analysis
            )
            self.logger.info(f"🆕 신규 이슈 제안 완료: {len(new_issue_suggestions)}개")
        except Exception as e:
            self.logger.error(f"❌ 신규 이슈 제안 실패: {str(e)}")
            raise
        
        # 6. 종합 분석 결과 구성
        try:
            self.logger.info("🔧 종합 분석 결과 구성 시작")
            
            # 6-1. 기본 메타데이터
            analysis_metadata = {
                "company_name": company_name,
                "analysis_year": current_year,
                "base_year": base_assessment.year,
                "analysis_date": datetime.now().isoformat(),
                "analysis_type": "news_based_change_analysis",
                "disclaimer": "이 분석은 뉴스 데이터를 기반으로 한 참고용 제안 사항입니다. 실제 중대성 평가에는 추가적인 검토가 필요합니다."
            }
            self.logger.info("✅ 6-1. 기본 메타데이터 완료")
            
            # 6-2. 뉴스 분석 요약
            news_analysis_summary = {
                "total_articles_analyzed": evolution_analysis['news_data_summary']['total_articles'],
                "analysis_period": evolution_analysis['news_data_summary']['analysis_period'],
                "overall_trend": evolution_analysis['overall_trend']['overall_direction'],
                "update_necessity": evolution_analysis['overall_trend']['update_necessity'],
                "confidence_level": evolution_analysis['overall_trend']['avg_confidence']
            }
            self.logger.info("✅ 6-2. 뉴스 분석 요약 완료")
            
            # 6-3. 변화 분석 (여기서 에러 가능성 높음)
            try:
                significant_changes = len([
                    change for change in evolution_analysis['topic_changes']
                    if abs(change['change_magnitude']) > self.analysis_params['significance_threshold']
                ])
                self.logger.info(f"✅ 6-3-a. 중요 변화 계산 완료: {significant_changes}개")
            except Exception as e:
                self.logger.error(f"❌ 6-3-a. 중요 변화 계산 실패: {str(e)}")
                raise
            
            change_analysis = {
                "existing_topics": priority_suggestions,
                "new_issues_discovered": new_issue_suggestions,
                "change_distribution": evolution_analysis['overall_trend']['change_distribution'],
                "significant_changes": significant_changes
            }
            self.logger.info("✅ 6-3. 변화 분석 완료")
            
            # 6-4. 액션 아이템 생성
            try:
                action_items = self._generate_action_items(evolution_analysis, recommendations)
                self.logger.info("✅ 6-4. 액션 아이템 생성 완료")
            except Exception as e:
                self.logger.error(f"❌ 6-4. 액션 아이템 생성 실패: {str(e)}")
                raise
            
            # 6-5. 신뢰도 평가
            try:
                confidence_assessment = self._assess_overall_confidence(evolution_analysis)
                self.logger.info("✅ 6-5. 신뢰도 평가 완료")
            except Exception as e:
                self.logger.error(f"❌ 6-5. 신뢰도 평가 실패: {str(e)}")
                raise
            
            # 6-6. 최종 결과 조합
            analysis_result = {
                "analysis_metadata": analysis_metadata,
                "news_analysis_summary": news_analysis_summary,
                "change_analysis": change_analysis,
                "recommendations": recommendations,
                "action_items": action_items,
                "confidence_assessment": confidence_assessment
            }
            
            self.logger.info("✅ 6. 종합 분석 결과 구성 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 6. 종합 분석 결과 구성 실패: {str(e)}")
            # 디버깅을 위한 상세 정보
            self.logger.error(f"🔍 evolution_analysis keys: {list(evolution_analysis.keys())}")
            if 'topic_changes' in evolution_analysis:
                self.logger.error(f"🔍 topic_changes 샘플: {evolution_analysis['topic_changes'][:1] if evolution_analysis['topic_changes'] else '빈 리스트'}")
            raise
        
            self.logger.info(f"✅ {company_name} 중대성 평가 변화 분석 완료")
            return analysis_result
        
        except Exception as e:
            self.logger.error(f"💥 전체 분석 프로세스 실패: {str(e)}")
            self.logger.error(f"💥 에러 타입: {type(e).__name__}")
            import traceback
            self.logger.error(f"💥 상세 스택 트레이스:\n{traceback.format_exc()}")
            raise
    
    async def _analyze_without_base_assessment(
        self,
        company_name: str,
        current_year: int
    ) -> Dict[str, Any]:
        """기준 평가 없이 뉴스 기반 이슈 분석"""
        self.logger.info(f"🆕 {company_name} 기준 평가 없음, 뉴스 기반 이슈 분석 수행")
        
        # 뉴스 데이터 수집
        news_data = await self.update_engine._collect_current_news_data(
            company_name, current_year
        )
        
        if not news_data['articles']:
            return {
                "analysis_metadata": {
                    "company_name": company_name,
                    "analysis_year": current_year,
                    "analysis_date": datetime.now().isoformat(),
                    "analysis_type": "insufficient_data",
                    "disclaimer": "뉴스 데이터가 충분하지 않아 분석을 수행할 수 없습니다."
                },
                "error": "insufficient_news_data",
                "message": "분석에 필요한 뉴스 데이터가 없습니다."
            }
        
        # 뉴스에서 핵심 이슈 추출
        core_issues = await self._extract_potential_issues_from_news(
            news_data['articles'], company_name
        )
        
        return {
            "analysis_metadata": {
                "company_name": company_name,
                "analysis_year": current_year,
                "analysis_date": datetime.now().isoformat(),
                "analysis_type": "news_only_analysis",
                "disclaimer": "기준 평가가 없어 뉴스 데이터만으로 분석했습니다. 실제 중대성 평가에는 추가 검토가 필요합니다."
            },
            "news_analysis_summary": {
                "total_articles_analyzed": len(news_data['articles']),
                "analysis_period": news_data['metadata']['period'],
                "core_issues_found": len(core_issues)
            },
            "potential_issues": core_issues,
            "recommendations": [
                "뉴스 분석 결과를 바탕으로 중대성 평가 초안을 검토하시기 바랍니다.",
                "발견된 이슈들에 대해 이해관계자와의 추가 논의가 필요합니다.",
                "SASB 매핑을 통해 산업 표준과의 일치성을 확인하시기 바랍니다."
            ],
            "confidence_assessment": {
                "overall_confidence": 0.5,
                "confidence_level": "medium",
                "limitations": [
                    "기준 평가 없음으로 변화 추세 분석 불가",
                    "뉴스 데이터만으로는 중대성 평가의 우선순위 결정 한계",
                    "이해관계자 의견 및 비즈니스 임팩트 분석 필요"
                ]
            }
        }
    
    def _generate_change_recommendations(
        self,
        evolution_analysis: Dict[str, Any],
        base_assessment: MaterialityAssessment
    ) -> List[Dict[str, Any]]:
        """변화 분석 기반 추천 사항 생성"""
        recommendations = []
        
        # 1. 높은 변화 토픽 추천
        high_change_topics = [
            change for change in evolution_analysis['topic_changes']
            if abs(change['change_magnitude']) > self.analysis_params['significance_threshold']
        ]
        
        for change in high_change_topics[:5]:  # 상위 5개
            rec_type = "priority_review"
            if change['change_magnitude'] > 0:
                action = "우선순위 상향 검토"
                rationale = f"뉴스 활동 증가 ({change['change_magnitude']:+.2f})"
            else:
                action = "우선순위 하향 검토"
                rationale = f"뉴스 활동 감소 ({change['change_magnitude']:+.2f})"
            
            recommendations.append({
                "type": rec_type,
                "topic_name": change['topic_name'],
                "current_priority": change['previous_priority'],
                "suggested_action": action,
                "rationale": rationale,
                "confidence": change['confidence'],
                "news_evidence": {
                    "total_articles": change['news_metrics']['total_articles'],
                    "relevant_articles": change['news_metrics']['relevant_articles'],
                    "avg_sentiment": change['news_metrics']['avg_sentiment']
                }
            })
        
        # 2. 신규 이슈 추천
        for new_issue in evolution_analysis['new_issues'][:3]:  # 상위 3개
            if new_issue['issue_score'] > self.analysis_params['new_issue_threshold']:
                recommendations.append({
                    "type": "new_issue_review",
                    "topic_name": new_issue['keyword'],
                    "suggested_action": "신규 중대성 이슈 검토",
                    "rationale": f"뉴스에서 {new_issue['frequency']}회 언급, 이슈 점수 {new_issue['issue_score']:.2f}",
                    "confidence": new_issue['confidence'],
                    "news_evidence": {
                        "frequency": new_issue['frequency'],
                        "related_articles": new_issue['related_articles_count'],
                        "sample_articles": new_issue.get('sample_articles', [])[:2]
                    }
                })
        
        # 3. 전체 트렌드 기반 추천
        overall_trend = evolution_analysis['overall_trend']
        if overall_trend['update_necessity'] == 'high':
            recommendations.append({
                "type": "overall_review",
                "suggested_action": "중대성 평가 전면 재검토",
                "rationale": f"전체 변화 강도 높음 ({overall_trend['avg_change_magnitude']:.2f})",
                "confidence": overall_trend['avg_confidence'],
                "scope": "comprehensive_review"
            })
        
        return recommendations[:self.analysis_params['max_recommendations']]
    
    def _generate_priority_suggestions(
        self,
        evolution_analysis: Dict[str, Any],
        base_assessment: MaterialityAssessment
    ) -> List[Dict[str, Any]]:
        """우선순위 변화 제안 생성"""
        suggestions = []
        
        for change in evolution_analysis['topic_changes']:
            current_priority = change['previous_priority']
            change_magnitude = change['change_magnitude']
            
            # 제안 우선순위 계산 (참고용)
            if change_magnitude > 0.3:
                suggested_direction = "상향 검토"
                suggested_change = min(3, int(change_magnitude * 5))
            elif change_magnitude < -0.3:
                suggested_direction = "하향 검토"
                suggested_change = max(-3, int(change_magnitude * 5))
            else:
                suggested_direction = "현재 수준 유지"
                suggested_change = 0
            
            suggestions.append({
                "topic_name": change['topic_name'],
                "current_priority": current_priority,
                "suggested_direction": suggested_direction,
                "suggested_change": suggested_change,
                "rationale": f"뉴스 분석 점수 변화: {change_magnitude:+.2f}",
                "confidence": change['confidence'],
                "change_type": change['change_type'],
                "supporting_evidence": change['reasons']
            })
        
        return suggestions
    
    def _generate_new_issue_suggestions(
        self,
        evolution_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """신규 이슈 검토 제안 생성"""
        suggestions = []
        
        for new_issue in evolution_analysis['new_issues']:
            if new_issue['issue_score'] > self.analysis_params['new_issue_threshold']:
                # SASB 매핑 정보
                sasb_mapping = new_issue.get('sasb_mapping', 'unmapped')
                
                suggestions.append({
                    "issue_name": new_issue['keyword'],
                    "discovery_rationale": new_issue['discovery_rationale'],
                    "issue_score": new_issue['issue_score'],
                    "frequency": new_issue['frequency'],
                    "confidence": new_issue['confidence'],
                    "sasb_relevance": sasb_mapping,
                    "suggested_action": "중대성 평가 포함 검토",
                    "review_priority": "high" if new_issue['issue_score'] > 0.6 else "medium",
                    "supporting_evidence": {
                        "related_articles": new_issue['related_articles_count'],
                        "sample_headlines": [
                            article.get('title', 'No title')
                            for article in new_issue.get('sample_articles', [])[:3]
                        ]
                    }
                })
        
        return suggestions
    
    def _generate_action_items(
        self,
        evolution_analysis: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """실행 가능한 액션 아이템 생성"""
        action_items = []
        
        # 1. 즉시 검토 필요 사항
        high_priority_items = [
            rec for rec in recommendations
            if rec.get('confidence', 0) > self.analysis_params['high_confidence_threshold']
        ]
        
        if high_priority_items:
            action_items.append({
                "priority": "immediate",
                "action": "높은 신뢰도 변화 사항 검토",
                "description": f"{len(high_priority_items)}개 항목에 대한 즉시 검토 필요",
                "timeline": "1주 이내",
                "responsible": "중대성 평가 담당팀",
                "items": [item['topic_name'] for item in high_priority_items]
            })
        
        # 2. 신규 이슈 검토
        new_issues_count = len(evolution_analysis['new_issues'])
        if new_issues_count > 0:
            action_items.append({
                "priority": "medium",
                "action": "신규 이슈 검토 및 평가",
                "description": f"{new_issues_count}개 신규 이슈에 대한 중대성 평가 필요성 검토",
                "timeline": "2주 이내",
                "responsible": "ESG 팀, 사업부 담당자",
                "items": [issue['keyword'] for issue in evolution_analysis['new_issues']]
            })
        
        # 3. 전체 업데이트 필요성
        if evolution_analysis['overall_trend']['update_necessity'] == 'high':
            action_items.append({
                "priority": "high",
                "action": "중대성 평가 전면 재검토",
                "description": "전체적인 변화 강도가 높아 중대성 평가 전면 재검토 필요",
                "timeline": "1개월 이내",
                "responsible": "중대성 평가 위원회",
                "scope": "comprehensive_review"
            })
        
        return action_items
    
    def _assess_overall_confidence(
        self,
        evolution_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """전체 분석 신뢰도 평가"""
        avg_confidence = evolution_analysis['overall_trend']['avg_confidence']
        news_count = evolution_analysis['news_data_summary']['total_articles']
        
        # 신뢰도 레벨 결정
        if avg_confidence > 0.7 and news_count > 50:
            confidence_level = "high"
            description = "분석 결과에 높은 신뢰도를 가질 수 있습니다"
        elif avg_confidence > 0.5 and news_count > 20:
            confidence_level = "medium"
            description = "분석 결과를 참고용으로 활용하시기 바랍니다"
        else:
            confidence_level = "low"
            description = "추가 데이터 수집 및 검토가 필요합니다"
        
        # 한계사항 식별
        limitations = []
        if news_count < 20:
            limitations.append("뉴스 데이터 부족으로 인한 분석 한계")
        if avg_confidence < 0.5:
            limitations.append("키워드 매칭 정확도 한계")
        
        limitations.extend([
            "뉴스 데이터만으로는 이해관계자 관점 반영 한계",
            "정량적 비즈니스 임팩트 분석 부족",
            "사업 전략 및 규제 변화 고려 필요"
        ])
        
        return {
            "overall_confidence": avg_confidence,
            "confidence_level": confidence_level,
            "description": description,
            "limitations": limitations,
            "recommendation": "뉴스 분석 결과를 바탕으로 이해관계자 의견 수렴 및 전문가 검토를 통해 최종 중대성 평가를 수행하시기 바랍니다."
        }
    
    async def _extract_potential_issues_from_news(
        self,
        news_articles: List[Dict[str, Any]],
        company_name: str
    ) -> List[Dict[str, Any]]:
        """뉴스에서 잠재적 중대성 이슈 추출"""
        # 키워드 빈도 분석
        keyword_frequency = defaultdict(int)
        keyword_articles = defaultdict(list)
        
        for article in news_articles:
            title = article.get('title', '')
            content = article.get('content', '') or article.get('summary', '')
            full_text = title + ' ' + content
            
            keywords = self.news_engine._extract_keywords_from_text(full_text)
            for keyword in keywords:
                if len(keyword) > 2:
                    keyword_frequency[keyword] += 1
                    keyword_articles[keyword].append(article)
        
        # 상위 키워드 분석
        top_keywords = sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)[:20]
        
        potential_issues = []
        for keyword, frequency in top_keywords:
            if frequency >= 2:
                related_articles = keyword_articles[keyword]
                issue_score = self.update_engine._calculate_new_issue_score(
                    related_articles, keyword, frequency
                )
                
                if issue_score > 0.2:
                    potential_issues.append({
                        "issue_name": keyword,
                        "frequency": frequency,
                        "relevance_score": issue_score,
                        "confidence": min(issue_score / 1.0, 1.0),
                        "related_articles_count": len(related_articles),
                        "review_suggestion": "중대성 평가 포함 검토 필요",
                        "sasb_mapping": self.mapping_service.get_sasb_code_by_topic(keyword)
                    })
        
        return sorted(potential_issues, key=lambda x: x['relevance_score'], reverse=True)[:10] 