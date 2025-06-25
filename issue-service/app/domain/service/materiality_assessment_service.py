import uuid
import json
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd

from app.domain.model.esg_issue_dto import ESGIssue
from app.domain.service.esg_issue_service import (
    load_local_ai_model, 
    classify_text_with_local_ai
)

logger = logging.getLogger(__name__)

@dataclass
class QuantitativeData:
    """정량데이터 구조"""
    revenue: float
    costs: float
    carbon_emissions: float
    water_usage: float
    waste_generation: float
    employee_count: int
    safety_incidents: int
    
@dataclass
class NewsData:
    """뉴스데이터 구조"""
    content: str
    source: str
    publish_date: datetime
    mentions: int
    audience_reach: int
    source_credibility: float
    
@dataclass
class MaterialityResult:
    """중대성평가 결과"""
    issue_id: str
    issue_text: str
    business_impact_score: float  # X축 (0-1)
    stakeholder_interest_score: float  # Y축 (0-1)
    materiality_level: str  # High/Medium/Low
    gri_mapping: str
    recommendations: List[str]

class MaterialityAssessmentService:
    """중대성평가 서비스"""
    
    def __init__(self):
        self.ai_model, self.tokenizer = load_local_ai_model()
        
    def calculate_business_impact(self, esg_issue: ESGIssue, quant_data: QuantitativeData) -> float:
        """비즈니스 임팩트 점수 계산 (X축)"""
        
        # GRI 카테고리별 가중치
        gri_weights = {
            "GRI 302: Energy": 0.9,  # 에너지 - 높은 비용 영향
            "GRI 305: Emissions": 0.85,  # 배출 - 규제 리스크
            "GRI 303: Water": 0.7,   # 수자원 - 운영 리스크
            "GRI 412: Human Rights": 0.8,  # 인권 - 평판 리스크
            "GRI 418: Customer Privacy": 0.75,  # 정보보호 - 법적 리스크
            "GRI 403: Occupational Health": 0.7,  # 안전보건
            "GRI 205: Anti-corruption": 0.8,  # 반부패
        }
        
        # 기본 가중치
        base_weight = gri_weights.get(esg_issue.mapped_gri, 0.5)
        
        # 정량데이터 기반 조정
        financial_factor = min(quant_data.costs / quant_data.revenue, 0.3) if quant_data.revenue > 0 else 0
        
        # 환경 영향 팩터
        env_factor = 0
        if "기후" in esg_issue.text or "탄소" in esg_issue.text:
            env_factor = min(quant_data.carbon_emissions / 1000000, 0.2)  # 정규화
            
        # 사회 영향 팩터  
        social_factor = 0
        if "안전" in esg_issue.text or "인권" in esg_issue.text:
            social_factor = min(quant_data.safety_incidents / 100, 0.2)
            
        # 최종 점수 계산
        business_impact = base_weight + financial_factor + env_factor + social_factor
        return min(business_impact, 1.0)
    
    def calculate_stakeholder_interest(self, esg_issue: ESGIssue, news_data_list: List[NewsData]) -> float:
        """이해관계자 관심도 점수 계산 (Y축)"""
        
        if not news_data_list:
            return esg_issue.score  # 뉴스가 없으면 기본 AI 점수 사용
            
        total_score = 0
        total_weight = 0
        
        for news in news_data_list:
            # AI 모델로 뉴스의 ESG 관련성 확인
            if self.ai_model and self.tokenizer:
                relevance = classify_text_with_local_ai(news.content, self.ai_model, self.tokenizer)
                if not relevance["is_esg"] or relevance["confidence"] < 0.6:
                    continue
                    
            # 미디어 노출도 계산
            media_score = min(news.mentions / 100, 0.3)  # 언급 횟수
            reach_score = min(news.audience_reach / 1000000, 0.3)  # 도달 범위
            credibility_score = news.source_credibility * 0.4  # 출처 신뢰도
            
            news_score = media_score + reach_score + credibility_score
            weight = news.source_credibility
            
            total_score += news_score * weight
            total_weight += weight
            
        if total_weight == 0:
            return esg_issue.score
            
        stakeholder_interest = total_score / total_weight
        return min(stakeholder_interest, 1.0)
    
    def classify_materiality_level(self, business_impact: float, stakeholder_interest: float) -> str:
        """중대성 수준 분류"""
        
        # 중대성 매트릭스 기준
        if business_impact >= 0.7 and stakeholder_interest >= 0.7:
            return "High"
        elif business_impact >= 0.5 and stakeholder_interest >= 0.5:
            return "Medium"
        else:
            return "Low"
    
    def generate_recommendations(self, materiality_result: MaterialityResult) -> List[str]:
        """중대성 수준별 권고사항 생성"""
        
        recommendations = []
        
        if materiality_result.materiality_level == "High":
            recommendations.extend([
                "🔥 최우선 관리 대상 - 즉시 대응 전략 수립 필요",
                "📊 정기적 모니터링 및 성과 측정 체계 구축",
                "💼 경영진 직접 관여 및 의사결정 필요",
                "📢 이해관계자 대상 투명한 커뮤니케이션 강화"
            ])
        elif materiality_result.materiality_level == "Medium":
            recommendations.extend([
                "⚠️ 중요 관리 대상 - 체계적 관리 방안 수립",
                "📈 성과 개선을 위한 구체적 액션플랜 필요",
                "🤝 관련 부서 간 협업 체계 구축"
            ])
        else:
            recommendations.extend([
                "📋 기본 관리 대상 - 현황 모니터링 지속",
                "🔍 향후 중대성 변화 추이 관찰 필요"
            ])
            
        # GRI별 특화 권고사항
        if materiality_result.gri_mapping == "GRI 302: Energy":
            recommendations.append("⚡ 에너지 효율 개선 및 재생에너지 전환 검토")
        elif materiality_result.gri_mapping == "GRI 305: Emissions":
            recommendations.append("🌱 탄소중립 로드맵 수립 및 배출권 관리 강화")
        elif materiality_result.gri_mapping == "GRI 412: Human Rights":
            recommendations.append("👥 인권 실사 체계 강화 및 교육 프로그램 확대")
            
        return recommendations
    
    def conduct_materiality_assessment(
        self, 
        esg_issues: List[ESGIssue], 
        quant_data: QuantitativeData,
        news_data_list: List[NewsData]
    ) -> List[MaterialityResult]:
        """통합 중대성평가 수행"""
        
        logger.info(f"🎯 중대성평가 시작: {len(esg_issues)}개 이슈 분석")
        
        results = []
        
        for issue in esg_issues:
            # 비즈니스 임팩트 계산
            business_impact = self.calculate_business_impact(issue, quant_data)
            
            # 이해관계자 관심도 계산
            stakeholder_interest = self.calculate_stakeholder_interest(issue, news_data_list)
            
            # 중대성 수준 분류
            materiality_level = self.classify_materiality_level(business_impact, stakeholder_interest)
            
            # 결과 객체 생성
            result = MaterialityResult(
                issue_id=issue.id,
                issue_text=issue.text,
                business_impact_score=round(business_impact, 3),
                stakeholder_interest_score=round(stakeholder_interest, 3),
                materiality_level=materiality_level,
                gri_mapping=issue.mapped_gri or "미분류",
                recommendations=[]
            )
            
            # 권고사항 생성
            result.recommendations = self.generate_recommendations(result)
            
            results.append(result)
            
        # 중대성 수준별 정렬 (High > Medium > Low)
        priority_order = {"High": 3, "Medium": 2, "Low": 1}
        results.sort(
            key=lambda x: (
                priority_order[x.materiality_level], 
                x.business_impact_score + x.stakeholder_interest_score
            ), 
            reverse=True
        )
        
        logger.info(f"✅ 중대성평가 완료: High({len([r for r in results if r.materiality_level == 'High'])}), "
                   f"Medium({len([r for r in results if r.materiality_level == 'Medium'])}), "
                   f"Low({len([r for r in results if r.materiality_level == 'Low'])})")
        
        return results
    
    def create_materiality_matrix_data(self, results: List[MaterialityResult]) -> Dict:
        """중대성 매트릭스 시각화용 데이터 생성"""
        
        matrix_data = {
            "high_materiality": [],
            "medium_materiality": [],
            "low_materiality": [],
            "matrix_points": []
        }
        
        for result in results:
            point = {
                "x": result.business_impact_score,
                "y": result.stakeholder_interest_score,
                "label": result.issue_text[:50] + "..." if len(result.issue_text) > 50 else result.issue_text,
                "level": result.materiality_level,
                "gri": result.gri_mapping
            }
            
            matrix_data["matrix_points"].append(point)
            matrix_data[f"{result.materiality_level.lower()}_materiality"].append(result)
            
        return matrix_data

def save_materiality_results(results: List[MaterialityResult], filename: str) -> str:
    """중대성평가 결과 저장"""
    from app.domain.service.esg_issue_service import OUTPUT_DIR
    import os
    
    path = os.path.join(OUTPUT_DIR, filename)
    
    # 결과를 딕셔너리로 변환
    results_dict = []
    for result in results:
        results_dict.append({
            "issue_id": result.issue_id,
            "issue_text": result.issue_text,
            "business_impact_score": result.business_impact_score,
            "stakeholder_interest_score": result.stakeholder_interest_score,
            "materiality_level": result.materiality_level,
            "gri_mapping": result.gri_mapping,
            "recommendations": result.recommendations
        })
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "assessment_date": datetime.now().isoformat(),
            "total_issues": len(results),
            "high_priority": len([r for r in results if r.materiality_level == "High"]),
            "medium_priority": len([r for r in results if r.materiality_level == "Medium"]),
            "low_priority": len([r for r in results if r.materiality_level == "Low"]),
            "results": results_dict
        }, f, ensure_ascii=False, indent=2)
    
    return path 