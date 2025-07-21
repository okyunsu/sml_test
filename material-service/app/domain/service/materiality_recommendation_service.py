from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from collections import defaultdict
import math

from ..model.materiality_dto import (
    MaterialityAssessment, MaterialityHistory, MaterialityTrendAnalysis,
    MaterialityUpdateRecommendation, IssueChangeType
)
from .materiality_mapping_service import MaterialityMappingService

logger = logging.getLogger(__name__)

class MaterialityRecommendationService:
    """중대성 평가 업데이트 제안 서비스
    
    이슈 분류 및 제안 기능:
    - 이슈 분류 (emerging/ongoing/maturing)
    - 내년도 중대성 평가 업데이트 제안
    - 우선순위 제안
    - SASB 연관성 분석
    - 뉴스 기반 신뢰도 평가
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mapping_service = MaterialityMappingService()
        
    def generate_update_recommendations(
        self, 
        trend_analysis: MaterialityTrendAnalysis,
        current_assessment: MaterialityAssessment,
        target_year: int
    ) -> List[MaterialityUpdateRecommendation]:
        """차년도 중대성 평가 업데이트 제안 생성
        
        Args:
            trend_analysis: 트렌드 분석 결과
            current_assessment: 현재 연도 평가
            target_year: 목표 연도 (차년도)
            
        Returns:
            List[MaterialityUpdateRecommendation]: 업데이트 제안 목록
        """
        self.logger.info(f"📋 {target_year}년도 중대성 평가 업데이트 제안 생성 시작")
        
        recommendations = []
        
        # 1. 부상 이슈 기반 제안
        emerging_recommendations = self._generate_emerging_recommendations(
            trend_analysis.emerging_issues, current_assessment, target_year
        )
        recommendations.extend(emerging_recommendations)
        
        # 2. 지속 이슈 기반 제안
        ongoing_recommendations = self._generate_ongoing_recommendations(
            trend_analysis.ongoing_issues, current_assessment, target_year
        )
        recommendations.extend(ongoing_recommendations)
        
        # 3. 성숙 이슈 기반 제안
        maturing_recommendations = self._generate_maturing_recommendations(
            trend_analysis.maturing_issues, current_assessment, target_year
        )
        recommendations.extend(maturing_recommendations)
        
        # 4. 뉴스 기반 신규 이슈 제안
        news_based_recommendations = self._generate_news_based_recommendations(
            trend_analysis.news_frequency_analysis, current_assessment, target_year
        )
        recommendations.extend(news_based_recommendations)
        
        # 5. 제안사항 우선순위 정렬 및 최종 검증
        final_recommendations = self._prioritize_and_validate_recommendations(recommendations)
        
        self.logger.info(f"✅ 총 {len(final_recommendations)}개의 업데이트 제안 생성 완료")
        return final_recommendations
    
    def classify_issue_importance(
        self, 
        topic_name: str, 
        trend_analysis: MaterialityTrendAnalysis,
        current_assessment: MaterialityAssessment
    ) -> Dict[str, Any]:
        """이슈 중요도 분류
        
        Args:
            topic_name: 토픽명
            trend_analysis: 트렌드 분석 결과
            current_assessment: 현재 평가
            
        Returns:
            Dict[str, Any]: 중요도 분류 결과
        """
        # 현재 우선순위 확인
        current_priority = None
        for topic in current_assessment.topics:
            if topic.topic_name == topic_name:
                current_priority = topic.priority
                break
        
        # 트렌드 분석에서 해당 토픽 정보 추출
        topic_change_info = None
        for change in trend_analysis.topic_changes:
            if change["topic_name"] == topic_name:
                topic_change_info = change
                break
        
        # 중요도 분류 계산
        importance_score = self._calculate_importance_score(
            topic_name, current_priority, topic_change_info, trend_analysis
        )
        
        # 분류 결과 생성
        classification = self._classify_by_score(importance_score)
        
        return {
            "topic_name": topic_name,
            "importance_score": importance_score,
            "classification": classification,
            "current_priority": current_priority,
            "trend_info": topic_change_info,
            "sasb_mapping": self.mapping_service.map_topic_to_sasb(topic_name),
            "recommendation_confidence": self._calculate_confidence_score(
                importance_score, topic_change_info, trend_analysis
            )
        }
    
    def _generate_emerging_recommendations(
        self, 
        emerging_issues: List[Dict[str, Any]], 
        current_assessment: MaterialityAssessment,
        target_year: int
    ) -> List[MaterialityUpdateRecommendation]:
        """부상 이슈 기반 제안 생성"""
        recommendations = []
        
        for issue in emerging_issues:
            topic_name = issue["topic_name"]
            
            # 현재 평가에서 해당 토픽 확인
            current_topic = None
            for topic in current_assessment.topics:
                if topic.topic_name == topic_name:
                    current_topic = topic
                    break
            
            # SASB 매핑 정보
            sasb_mapping = self.mapping_service.map_topic_to_sasb(topic_name)
            sasb_info = sasb_mapping[0] if sasb_mapping else None
            
            # 관련 키워드 추출
            related_keywords = self._extract_related_keywords(topic_name)
            
            # 뉴스 건수 추정 (simulated)
            news_count = self._estimate_news_count(topic_name)
            
            # 제안 근거 생성
            rationale = self._generate_emerging_rationale(issue, current_topic, sasb_info)
            
            # 신뢰도 점수 계산
            confidence_score = self._calculate_emerging_confidence(issue, sasb_info, news_count)
            
            recommendation = MaterialityUpdateRecommendation(
                topic_name=topic_name,
                change_type=IssueChangeType.EMERGING,
                rationale=rationale,
                related_keywords=related_keywords,
                news_count=news_count,
                confidence_score=confidence_score,
                sasb_alignment=sasb_info.sasb_name if sasb_info else "매핑 정보 없음"
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_ongoing_recommendations(
        self, 
        ongoing_issues: List[Dict[str, Any]], 
        current_assessment: MaterialityAssessment,
        target_year: int
    ) -> List[MaterialityUpdateRecommendation]:
        """지속 이슈 기반 제안 생성"""
        recommendations = []
        
        for issue in ongoing_issues:
            topic_name = issue["topic_name"]
            
            # 지속 이슈는 기존 관리 체계 유지 제안
            sasb_mapping = self.mapping_service.map_topic_to_sasb(topic_name)
            sasb_info = sasb_mapping[0] if sasb_mapping else None
            
            related_keywords = self._extract_related_keywords(topic_name)
            news_count = self._estimate_news_count(topic_name)
            
            rationale = (
                f"지속적으로 관리되는 핵심 이슈로 평균 우선순위 {issue['avg_priority']:.1f}위, "
                f"일관성 점수 {issue['consistency_score']:.2f}를 기록. "
                f"안정적인 관리 체계 유지가 필요한 상황입니다."
            )
            
            confidence_score = issue['consistency_score'] * 0.8  # 일관성 기반 신뢰도
            
            recommendation = MaterialityUpdateRecommendation(
                topic_name=topic_name,
                change_type=IssueChangeType.ONGOING,
                rationale=rationale,
                related_keywords=related_keywords,
                news_count=news_count,
                confidence_score=confidence_score,
                sasb_alignment=sasb_info.sasb_name if sasb_info else "매핑 정보 없음"
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_maturing_recommendations(
        self, 
        maturing_issues: List[Dict[str, Any]], 
        current_assessment: MaterialityAssessment,
        target_year: int
    ) -> List[MaterialityUpdateRecommendation]:
        """성숙 이슈 기반 제안 생성"""
        recommendations = []
        
        for issue in maturing_issues:
            topic_name = issue["topic_name"]
            
            sasb_mapping = self.mapping_service.map_topic_to_sasb(topic_name)
            sasb_info = sasb_mapping[0] if sasb_mapping else None
            
            related_keywords = self._extract_related_keywords(topic_name)
            news_count = self._estimate_news_count(topic_name)
            
            # 성숙 이슈 유형에 따른 제안
            if issue["declining_trend"]:
                change_type = IssueChangeType.DECLINING
                rationale = (
                    f"우선순위 하락 추세를 보이는 성숙 이슈로 성숙도 점수 {issue['maturity_score']:.2f}를 기록. "
                    f"중대성 평가 범위 재검토 또는 관리 우선순위 조정이 필요합니다."
                )
            else:
                change_type = IssueChangeType.MATURING
                rationale = (
                    f"성숙 단계에 진입한 이슈로 안정적인 관리 체계가 구축된 상태. "
                    f"현재 수준의 관리 유지 또는 효율성 개선에 집중할 시점입니다."
                )
            
            confidence_score = issue['maturity_score'] * 0.6  # 성숙도 기반 신뢰도
            
            recommendation = MaterialityUpdateRecommendation(
                topic_name=topic_name,
                change_type=change_type,
                rationale=rationale,
                related_keywords=related_keywords,
                news_count=news_count,
                confidence_score=confidence_score,
                sasb_alignment=sasb_info.sasb_name if sasb_info else "매핑 정보 없음"
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_news_based_recommendations(
        self, 
        news_analysis: Dict[str, Any], 
        current_assessment: MaterialityAssessment,
        target_year: int
    ) -> List[MaterialityUpdateRecommendation]:
        """뉴스 기반 신규 이슈 제안 생성"""
        recommendations = []
        
        # 트렌딩 키워드 기반 신규 이슈 제안
        trending_keywords = news_analysis.get("trending_keywords", [])
        current_topics = {topic.topic_name for topic in current_assessment.topics}
        
        for keyword in trending_keywords[:3]:  # 상위 3개 키워드
            # 키워드를 토픽으로 변환
            potential_topic = self._convert_keyword_to_topic(keyword)
            
            # 현재 평가에 없는 새로운 토픽인지 확인
            if potential_topic not in current_topics:
                sasb_mapping = self.mapping_service.map_topic_to_sasb(potential_topic)
                sasb_info = sasb_mapping[0] if sasb_mapping else None
                
                related_keywords = self._extract_related_keywords(potential_topic)
                news_count = self._estimate_news_count(potential_topic)
                
                rationale = (
                    f"뉴스 분석을 통해 식별된 부상 키워드 '{keyword}'와 관련된 이슈. "
                    f"미디어 관심도 증가 추세를 보이며, 향후 중대성 평가 고려가 필요합니다."
                )
                
                confidence_score = 0.7  # 뉴스 기반 제안의 기본 신뢰도
                
                recommendation = MaterialityUpdateRecommendation(
                    topic_name=potential_topic,
                    change_type=IssueChangeType.NEW,
                    rationale=rationale,
                    related_keywords=related_keywords,
                    news_count=news_count,
                    confidence_score=confidence_score,
                    sasb_alignment=sasb_info.sasb_name if sasb_info else "매핑 정보 없음"
                )
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def _prioritize_and_validate_recommendations(
        self, 
        recommendations: List[MaterialityUpdateRecommendation]
    ) -> List[MaterialityUpdateRecommendation]:
        """제안사항 우선순위 정렬 및 검증"""
        # 1. 신뢰도 점수 기반 정렬
        sorted_recommendations = sorted(
            recommendations, 
            key=lambda x: x.confidence_score, 
            reverse=True
        )
        
        # 2. 중복 제거
        unique_recommendations = []
        seen_topics = set()
        
        for rec in sorted_recommendations:
            if rec.topic_name not in seen_topics:
                unique_recommendations.append(rec)
                seen_topics.add(rec.topic_name)
        
        # 3. 상위 10개로 제한
        return unique_recommendations[:10]
    
    def _calculate_importance_score(
        self, 
        topic_name: str, 
        current_priority: Optional[int], 
        topic_change_info: Optional[Dict[str, Any]], 
        trend_analysis: MaterialityTrendAnalysis
    ) -> float:
        """중요도 점수 계산"""
        score = 0.0
        
        # 1. 현재 우선순위 점수 (높을수록 중요)
        if current_priority:
            score += (11 - current_priority) / 10 * 0.3
        
        # 2. 변화 추세 점수
        if topic_change_info:
            change_rate = abs(topic_change_info.get("change_rate", 0))
            score += min(change_rate, 1.0) * 0.3
        
        # 3. SASB 연관성 점수
        sasb_mapping = self.mapping_service.map_topic_to_sasb(topic_name)
        if sasb_mapping:
            score += 0.2
        
        # 4. 뉴스 빈도 점수
        news_count = self._estimate_news_count(topic_name)
        score += min(news_count / 100, 1.0) * 0.2
        
        return min(score, 1.0)
    
    def _classify_by_score(self, score: float) -> str:
        """점수 기반 분류"""
        if score >= 0.8:
            return "매우 중요"
        elif score >= 0.6:
            return "중요"
        elif score >= 0.4:
            return "보통"
        elif score >= 0.2:
            return "낮음"
        else:
            return "매우 낮음"
    
    def _calculate_confidence_score(
        self, 
        importance_score: float, 
        topic_change_info: Optional[Dict[str, Any]], 
        trend_analysis: MaterialityTrendAnalysis
    ) -> float:
        """신뢰도 점수 계산"""
        confidence = importance_score * 0.5
        
        # 변화 안정성 추가
        if topic_change_info:
            stability = topic_change_info.get("stability", 0)
            confidence += stability * 0.3
        
        # 데이터 품질 추가
        confidence += 0.2  # 기본 데이터 품질
        
        return min(confidence, 1.0)
    
    def _extract_related_keywords(self, topic_name: str) -> List[str]:
        """관련 키워드 추출"""
        # 실제 구현에서는 키워드 매핑 테이블 사용
        keyword_mapping = {
            "기후변화 대응": ["탄소중립", "온실가스", "RE100"],
            "에너지 효율": ["에너지절약", "효율개선", "스마트그리드"],
            "안전관리": ["중대재해", "산업안전", "안전보건"],
            "공급망 관리": ["공급망", "협력업체", "리스크관리"]
        }
        
        return keyword_mapping.get(topic_name, [topic_name])
    
    def _estimate_news_count(self, topic_name: str) -> int:
        """뉴스 건수 추정 (simulated)"""
        # 실제 구현에서는 sasb-service와 연동
        base_counts = {
            "기후변화 대응": 145,
            "에너지 효율": 123,
            "안전관리": 98,
            "공급망 관리": 87
        }
        
        return base_counts.get(topic_name, 50)  # 기본값 50
    
    def _generate_emerging_rationale(
        self, 
        issue: Dict[str, Any], 
        current_topic: Optional[Any], 
        sasb_info: Optional[Any]
    ) -> str:
        """부상 이슈 제안 근거 생성"""
        rationale = f"최근 {issue['year']}년 신규 등장하여 {issue['priority']}위의 높은 우선순위를 기록한 부상 이슈입니다."
        
        if sasb_info:
            rationale += f" SASB {sasb_info.sasb_category} 카테고리의 '{sasb_info.sasb_name}' 이슈와 연관됩니다."
        
        rationale += " 차년도 중대성 평가에서 중점적인 관리와 모니터링이 필요합니다."
        
        return rationale
    
    def _calculate_emerging_confidence(
        self, 
        issue: Dict[str, Any], 
        sasb_info: Optional[Any], 
        news_count: int
    ) -> float:
        """부상 이슈 신뢰도 계산"""
        confidence = 0.0
        
        # 우선순위 기반 신뢰도
        priority_score = (11 - issue['priority']) / 10 if issue['priority'] <= 10 else 0
        confidence += priority_score * 0.4
        
        # 부상 점수 기반 신뢰도
        emergence_score = issue.get('emergence_score', 0)
        confidence += emergence_score * 0.3
        
        # SASB 연관성 기반 신뢰도
        if sasb_info:
            confidence += 0.2
        
        # 뉴스 빈도 기반 신뢰도
        news_score = min(news_count / 100, 1.0)
        confidence += news_score * 0.1
        
        return min(confidence, 1.0)
    
    def _convert_keyword_to_topic(self, keyword: str) -> str:
        """키워드를 토픽으로 변환"""
        # 키워드 -> 토픽 변환 매핑
        keyword_to_topic = {
            "탄소중립": "기후변화 대응",
            "RE100": "재생에너지 전환",
            "ESG": "지속가능경영",
            "중대재해": "안전관리"
        }
        
        return keyword_to_topic.get(keyword, f"{keyword} 관련 이슈") 