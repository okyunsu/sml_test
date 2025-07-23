"""
분석 헬퍼 모듈
Material Service와 SASB Service에서 공통으로 사용하는 복잡한 분석 로직
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class MaterialityAnalysisHelper:
    """중대성 평가 분석 헬퍼 클래스"""
    
    @staticmethod
    def create_analysis_metadata(
        company_name: str,
        analysis_year: int,
        base_year: Optional[int] = None,
        status: str = "success"
    ) -> Dict[str, Any]:
        """분석 메타데이터 생성"""
        return {
            "company_name": company_name,
            "analysis_year": analysis_year,
            "base_year": base_year or 2024,
            "analysis_date": datetime.now().isoformat(),
            "analysis_type": "materiality_change_analysis",
            "status": status,
            "disclaimer": "뉴스 분석 결과는 참고용이며, 실제 중대성 평가는 다양한 이해관계자 의견을 종합하여 수행해야 합니다."
        }
    
    @staticmethod
    def create_news_analysis_summary(evolution_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 분석 요약 생성"""
        try:
            news_data = evolution_analysis.get('news_data_summary', {})
            overall_trend = evolution_analysis.get('overall_trend', {})
            
            return {
                "total_articles_analyzed": news_data.get('total_articles', 0),
                "analysis_period": news_data.get('analysis_period', 'unknown'),
                "overall_trend": overall_trend.get('overall_direction', 'neutral'),
                "update_necessity": overall_trend.get('update_necessity', False),
                "confidence_level": overall_trend.get('avg_confidence', 0.0)
            }
        except Exception as e:
            logger.error(f"뉴스 분석 요약 생성 실패: {e}")
            return {
                "total_articles_analyzed": 0,
                "analysis_period": "unknown",
                "overall_trend": "neutral",
                "update_necessity": False,
                "confidence_level": 0.0
            }
    
    @staticmethod
    def calculate_significant_changes(
        evolution_analysis: Dict[str, Any],
        significance_threshold: float = 0.3
    ) -> int:
        """중요한 변화 계산"""
        try:
            topic_changes = evolution_analysis.get('topic_changes', [])
            significant_changes = len([
                change for change in topic_changes
                if abs(change.get('change_magnitude', 0)) > significance_threshold
            ])
            logger.info(f"중요 변화 계산 완료: {significant_changes}개")
            return significant_changes
        except Exception as e:
            logger.error(f"중요 변화 계산 실패: {e}")
            return 0
    
    @staticmethod
    def create_change_analysis(
        evolution_analysis: Dict[str, Any],
        priority_suggestions: List[Dict[str, Any]],
        significance_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """변화 분석 결과 생성"""
        try:
            significant_changes = MaterialityAnalysisHelper.calculate_significant_changes(
                evolution_analysis, significance_threshold
            )
            
            # 평균 신뢰도 계산
            avg_confidence = 0.0
            if priority_suggestions:
                total_confidence = sum(topic.get('confidence', 0) for topic in priority_suggestions)
                avg_confidence = total_confidence / len(priority_suggestions)
            
            news_data = evolution_analysis.get('news_data_summary', {})
            overall_trend = evolution_analysis.get('overall_trend', {})
            
            return {
                "existing_topics": priority_suggestions,
                "topic_analysis_summary": {
                    "total_topics_analyzed": len(priority_suggestions),
                    "topics_with_significant_change": significant_changes,
                    "average_confidence": avg_confidence,
                    "news_coverage": {
                        "total_articles_analyzed": news_data.get('total_articles', 0),
                        "analysis_period": news_data.get('analysis_period', 'unknown')
                    }
                },
                "change_distribution": overall_trend.get('change_distribution', {}),
                "significant_changes": significant_changes
            }
        except Exception as e:
            logger.error(f"변화 분석 생성 실패: {e}")
            return {
                "existing_topics": [],
                "topic_analysis_summary": {
                    "total_topics_analyzed": 0,
                    "topics_with_significant_change": 0,
                    "average_confidence": 0.0,
                    "news_coverage": {
                        "total_articles_analyzed": 0,
                        "analysis_period": "unknown"
                    }
                },
                "change_distribution": {},
                "significant_changes": 0
            }

class AnalysisErrorHandler:
    """분석 에러 처리 클래스"""
    
    @staticmethod
    def create_error_response(
        company_name: str,
        analysis_year: int,
        error: Exception,
        context: str = "general"
    ) -> Dict[str, Any]:
        """에러 응답 생성"""
        import traceback
        
        error_type = type(error).__name__
        error_message = str(error)
        
        logger.error(f"{context} 분석 실패: {error_message}")
        logger.error(f"에러 타입: {error_type}")
        logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
        
        return {
            "analysis_metadata": {
                "company_name": company_name,
                "analysis_year": analysis_year,
                "analysis_date": datetime.now().isoformat(),
                "error": error_message,
                "status": "failure"
            },
            "error_details": {
                "error_type": error_type,
                "error_message": error_message,
                "context": context,
                "suggested_action": "서비스 관리자에게 문의하세요"
            }
        }
    
    @staticmethod
    def safe_execute(func, *args, context: str = "unknown", **kwargs):
        """안전한 함수 실행"""
        try:
            result = func(*args, **kwargs)
            logger.info(f"✅ {context} 성공")
            return result, None
        except Exception as e:
            logger.error(f"❌ {context} 실패: {str(e)}")
            return None, e

class ActionItemGenerator:
    """액션 아이템 생성 클래스"""
    
    @staticmethod
    def generate_action_items(
        evolution_analysis: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """액션 아이템 생성"""
        try:
            action_items = []
            
            # 1. 높은 우선순위 변화 기반 액션 아이템
            topic_changes = evolution_analysis.get('topic_changes', [])
            high_priority_changes = [
                change for change in topic_changes
                if abs(change.get('change_magnitude', 0)) > 0.5
            ]
            
            for change in high_priority_changes:
                action_items.append({
                    "type": "priority_review",
                    "title": f"{change.get('topic_name', 'Unknown')} 우선순위 재검토",
                    "description": f"변화 규모: {change.get('change_magnitude', 0):.2f}",
                    "urgency": "high",
                    "estimated_effort": "medium"
                })
            
            # 2. 추천사항 기반 액션 아이템
            for rec in recommendations[:3]:  # 상위 3개만
                action_items.append({
                    "type": "recommendation_review",
                    "title": f"{rec.get('title', 'Unknown')} 검토",
                    "description": rec.get('description', ''),
                    "urgency": "medium",
                    "estimated_effort": "low"
                })
            
            # 3. 기본 액션 아이템
            if not action_items:
                action_items.append({
                    "type": "routine_review",
                    "title": "정기 중대성 평가 검토",
                    "description": "연간 중대성 평가 검토 수행",
                    "urgency": "low",
                    "estimated_effort": "high"
                })
            
            logger.info(f"액션 아이템 {len(action_items)}개 생성 완료")
            return action_items
            
        except Exception as e:
            logger.error(f"액션 아이템 생성 실패: {e}")
            return [{
                "type": "error_recovery",
                "title": "분석 결과 검토",
                "description": "분석 중 오류가 발생했습니다. 수동 검토가 필요합니다.",
                "urgency": "medium",
                "estimated_effort": "high"
            }]

class ConfidenceAssessment:
    """신뢰도 평가 클래스"""
    
    @staticmethod
    def assess_overall_confidence(evolution_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """전체 신뢰도 평가"""
        try:
            news_data = evolution_analysis.get('news_data_summary', {})
            overall_trend = evolution_analysis.get('overall_trend', {})
            
            # 뉴스 데이터 신뢰도
            article_count = news_data.get('total_articles', 0)
            data_confidence = min(article_count / 50, 1.0)  # 50개 이상이면 최대 신뢰도
            
            # 분석 신뢰도
            analysis_confidence = overall_trend.get('avg_confidence', 0.0)
            
            # 전체 신뢰도 (가중 평균)
            overall_confidence = (data_confidence * 0.4 + analysis_confidence * 0.6)
            
            # 신뢰도 등급
            if overall_confidence >= 0.8:
                confidence_grade = "높음"
            elif overall_confidence >= 0.6:
                confidence_grade = "보통"
            elif overall_confidence >= 0.4:
                confidence_grade = "낮음"
            else:
                confidence_grade = "매우 낮음"
            
            return {
                "overall_confidence_score": overall_confidence,
                "confidence_grade": confidence_grade,
                "data_confidence": data_confidence,
                "analysis_confidence": analysis_confidence,
                "confidence_factors": {
                    "article_count": article_count,
                    "analysis_depth": len(evolution_analysis.get('topic_changes', [])),
                    "data_recency": news_data.get('analysis_period', 'unknown')
                },
                "recommendations": ConfidenceAssessment._get_confidence_recommendations(overall_confidence)
            }
            
        except Exception as e:
            logger.error(f"신뢰도 평가 실패: {e}")
            return {
                "overall_confidence_score": 0.0,
                "confidence_grade": "알 수 없음",
                "data_confidence": 0.0,
                "analysis_confidence": 0.0,
                "confidence_factors": {},
                "recommendations": ["분석 신뢰도를 확인할 수 없습니다."]
            }
    
    @staticmethod
    def _get_confidence_recommendations(confidence_score: float) -> List[str]:
        """신뢰도별 권장사항"""
        if confidence_score >= 0.8:
            return ["분석 결과를 중대성 평가 업데이트 검토에 활용할 수 있습니다."]
        elif confidence_score >= 0.6:
            return [
                "분석 결과를 참고하되, 추가 데이터 수집을 권장합니다.",
                "이해관계자 의견 수렴과 병행하여 검토하세요."
            ]
        elif confidence_score >= 0.4:
            return [
                "분석 결과는 초기 검토용으로만 사용하세요.",
                "더 많은 뉴스 데이터 수집이 필요합니다.",
                "전문가 의견을 반드시 포함하세요."
            ]
        else:
            return [
                "현재 분석 결과는 신뢰도가 낮습니다.",
                "데이터 소스를 다양화하고 분석 기간을 확장하세요.",
                "수동 분석을 병행하는 것을 권장합니다."
            ] 