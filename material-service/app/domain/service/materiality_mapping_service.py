from typing import Dict, List, Optional, Set, Any
from ..model.materiality_dto import SASBMaterialityMapping, MaterialityTopic
import logging

logger = logging.getLogger(__name__)

class MaterialityMappingService:
    """중대성 평가 토픽과 SASB 이슈 간의 매핑을 관리하는 서비스
    
    sasb-service의 기존 키워드 시스템을 활용하여 통합된 매핑 제공:
    - 산업 키워드 33개 (RENEWABLE_DOMAIN_KEYWORDS)
    - SASB 이슈 키워드 53개 (SASB_ISSUE_KEYWORDS)
    - 상세한 SASB 카테고리별 매핑 (E, S, G)
    """
    
    def __init__(self):
        # sasb-service의 산업 키워드 (33개)
        self.industry_keywords = self._get_industry_keywords()
        
        # sasb-service의 SASB 이슈 키워드 (53개) 
        self.sasb_issue_keywords = self._get_sasb_issue_keywords()
        
        # 상세한 SASB 매핑 테이블
        self.mapping_table = self._initialize_mapping_table()
        self.reverse_mapping = self._create_reverse_mapping()
    
    def _get_industry_keywords(self) -> List[str]:
        """sasb-service의 신재생에너지 산업 키워드 (33개)"""
        return [
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
    
    def _get_sasb_issue_keywords(self) -> List[str]:
        """sasb-service의 SASB 이슈 키워드 (53개)"""
        return [
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

    def _initialize_mapping_table(self) -> Dict[str, SASBMaterialityMapping]:
        """sasb-service 키워드 시스템 기반 매핑 테이블 생성"""
        mappings = {
            "E-GHG": SASBMaterialityMapping(
                sasb_code="E-GHG",
                sasb_name="Greenhouse Gas Emissions & Energy Resource Planning",
                sasb_category="E",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "기후변화 대응", "탄소중립", "온실가스 감축", "에너지 전환",
                    # sasb-service 키워드 연결
                    "탄소배출", "RE100", "CF100", "에너지믹스", "전원구성",
                    "탄소국경세", "스코프", "감축목표", "NDC", "자발적 탄소시장"
                ]
            ),
            "E-AIR": SASBMaterialityMapping(
                sasb_code="E-AIR",
                sasb_name="Air Quality",
                sasb_category="E",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "대기환경 보호", "대기질 관리", "배출가스 저감",
                    # sasb-service 키워드 연결
                    "미세먼지", "대기오염", "황산화물", "질소산화물", "바이오매스", "비산먼지"
                ]
            ),
            "E-WASTE": SASBMaterialityMapping(
                sasb_code="E-WASTE",
                sasb_name="Waste & Byproduct Management",
                sasb_category="E",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "순환경제", "폐기물 관리", "자원 재활용", "폐배터리 관리",
                    # sasb-service 키워드 연결
                    "폐배터리", "폐패널", "폐블레이드", "자원순환", "재활용", "재사용",
                    "핵심광물", "희토류"
                ]
            ),
            "E-WATER": SASBMaterialityMapping(
                sasb_code="E-WATER",
                sasb_name="Water Management",
                sasb_category="E",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "용수관리", "수자원 관리", "물 사용량 관리",
                    # sasb-service 키워드 연결
                    "수처리", "폐수", "수질오염", "냉각수", "수력발전", "그린수소", "수전해", "해양생태계"
                ]
            ),
            "E-ENERGY": SASBMaterialityMapping(
                sasb_code="E-ENERGY",
                sasb_name="End-Use Efficiency & Demand",
                sasb_category="E",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "에너지 효율 향상", "제품 에너지 효율 향상 및 환경영향 감소",
                    "에너지 효율화", "전력 효율성",
                    # sasb-service 키워드 연결
                    "에너지효율", "수요관리", "DR", "가상발전소", "VPP", "분산에너지", "스마트그리드"
                ]
            ),
            "E-GRID": SASBMaterialityMapping(
                sasb_code="E-GRID",
                sasb_name="Grid Resiliency",
                sasb_category="E",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "전력망 안정성", "계통 연계", "전력 품질",
                    # sasb-service 키워드 연결
                    "전력망", "계통안정", "출력제어", "출력제한", "간헐성", "주파수", "송배전망"
                ]
            ),
            "E-PRODUCT": SASBMaterialityMapping(
                sasb_code="E-PRODUCT",
                sasb_name="Product Environmental Impact",
                sasb_category="E",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "제품 환경영향 저감", "친환경 제품 개발", "제품 생애주기 평가",
                    # sasb-service 산업 키워드 연결
                    "신재생에너지", "재생에너지", "청정에너지", "친환경에너지"
                ]
            ),
            "S-SAFETY": SASBMaterialityMapping(
                sasb_code="S-SAFETY",
                sasb_name="Workforce Health & Safety",
                sasb_category="S",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "사업장 안전보건", "안전한 작업환경", "산업안전", "근로자 안전",
                    # sasb-service 키워드 연결
                    "중대재해", "산업재해", "감전사고", "추락사고", "중대재해처벌법", "안전보건"
                ]
            ),
            "S-INCIDENT": SASBMaterialityMapping(
                sasb_code="S-INCIDENT",
                sasb_name="Critical Incident Management",
                sasb_category="S",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "비상사태 관리", "사고 대응", "위기 관리",
                    # sasb-service 키워드 연결
                    "ESS화재", "폭발", "대규모정전", "블랙아웃", "자연재해", "댐붕괴", "안전진단"
                ]
            ),
            "S-LABOR": SASBMaterialityMapping(
                sasb_code="S-LABOR",
                sasb_name="Labor Relations & Human Rights",
                sasb_category="S",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "고용 및 노사관계", "인재 확보 및 유지", "공정한 인사제도 및 복리후생",
                    "노동권 보호", "인권 경영"
                ]
            ),
            "S-SUPPLY": SASBMaterialityMapping(
                sasb_code="S-SUPPLY",
                sasb_name="Supply Chain Management",
                sasb_category="S",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "지속가능한 공급망 관리", "공급망 관리 및 상생경영",
                    "협력사 관리", "공급망 ESG"
                ]
            ),
            "S-COMMUNITY": SASBMaterialityMapping(
                sasb_code="S-COMMUNITY",
                sasb_name="Community Relations",
                sasb_category="S",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "지역사회공헌", "사회공헌", "지역사회 관계", "사회적 가치 창출",
                    # sasb-service 키워드 연결
                    "입지갈등", "주민수용성", "환경영향평가", "산림훼손", "이격거리", 
                    "소음", "빛반사", "조류충돌", "공청회", "이익공유제"
                ]
            ),
            "S-PRODUCT": SASBMaterialityMapping(
                sasb_code="S-PRODUCT",
                sasb_name="Product Safety & Quality",
                sasb_category="S",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "고객 안전 및 보건", "제품 안전성", "품질 관리", "고객 만족"
                ]
            ),
            "S-AFFORDABILITY": SASBMaterialityMapping(
                sasb_code="S-AFFORDABILITY",
                sasb_name="Energy Affordability",
                sasb_category="S",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "에너지 접근성", "전력 요금 안정성", "에너지 형평성",
                    # sasb-service 키워드 연결
                    "전기요금", "에너지복지", "SMP", "REC", "PPA", "그리드패리티", "에너지빈곤층"
                ]
            ),
            "G-ETHICS": SASBMaterialityMapping(
                sasb_code="G-ETHICS",
                sasb_name="Business Ethics & Transparency",
                sasb_category="G",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "반부패 윤리경영 강화", "윤리경영 및 준법경영", "투명한 경영",
                    "컴플라이언스", "부패 방지"
                ]
            ),
            "G-GOVERNANCE": SASBMaterialityMapping(
                sasb_code="G-GOVERNANCE",
                sasb_name="Corporate Governance",
                sasb_category="G",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "건전한 이사회 구성", "기업지배구조", "이사회 독립성", "지배구조 투명성"
                ]
            ),
            "G-INNOVATION": SASBMaterialityMapping(
                sasb_code="G-INNOVATION",
                sasb_name="Innovation & Technology Development",
                sasb_category="G",
                materiality_topics=[
                    # 기업 중대성 평가 토픽
                    "신사업 발굴 및 친환경 기술 확보", "기술 혁신", "R&D 투자", "신기술 개발"
                ]
            )
        }
        return mappings
    
    def _create_reverse_mapping(self) -> Dict[str, str]:
        """토픽명에서 SASB 코드로의 역매핑 생성"""
        reverse_map = {}
        for sasb_code, mapping in self.mapping_table.items():
            for topic in mapping.materiality_topics:
                reverse_map[topic] = sasb_code
        return reverse_map
    
    def get_sasb_code_by_topic(self, topic_name: str) -> Optional[str]:
        """토픽명을 통해 SASB 코드 조회"""
        # 정확한 매치 먼저 시도
        if topic_name in self.reverse_mapping:
            return self.reverse_mapping[topic_name]
        
        # 부분 매치 시도 (유사한 키워드 포함)
        for mapped_topic, sasb_code in self.reverse_mapping.items():
            if self._calculate_similarity(topic_name, mapped_topic) > 0.7:
                logger.info(f"유사 매핑 발견: '{topic_name}' -> '{mapped_topic}' -> {sasb_code}")
                return sasb_code
        
        logger.warning(f"매핑되지 않은 토픽: '{topic_name}'")
        return None
    
    def map_topic_to_sasb(self, topic_name: str) -> List[SASBMaterialityMapping]:
        """토픽명을 통해 SASB 매핑 정보 조회"""
        sasb_code = self.get_sasb_code_by_topic(topic_name)
        if not sasb_code:
            return []
        
        mapping = self.mapping_table.get(sasb_code)
        if not mapping:
            return []
        
        return [mapping]
    
    def auto_map_topics(self, topics: List[MaterialityTopic]) -> List[MaterialityTopic]:
        """토픽 리스트에 자동으로 SASB 매핑 적용"""
        mapped_topics = []
        for topic in topics:
            sasb_code = self.get_sasb_code_by_topic(topic.topic_name)
            topic.sasb_mapping = sasb_code
            mapped_topics.append(topic)
        return mapped_topics
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """간단한 문자열 유사도 계산"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_industry_keywords(self) -> List[str]:
        """산업 키워드 목록 반환 (sasb-service 연동)"""
        return self.industry_keywords
    
    def get_sasb_issue_keywords(self) -> List[str]:
        """SASB 이슈 키워드 목록 반환 (sasb-service 연동)"""
        return self.sasb_issue_keywords
    
    def find_related_keywords(self, topic_name: str) -> Dict[str, List[str]]:
        """토픽과 관련된 키워드 찾기"""
        sasb_code = self.get_sasb_code_by_topic(topic_name)
        if not sasb_code:
            return {"industry_keywords": [], "sasb_keywords": []}
        
        mapping = self.mapping_table.get(sasb_code)
        if not mapping:
            return {"industry_keywords": [], "sasb_keywords": []}
        
        # 관련 키워드 찾기
        related_industry = []
        related_sasb = []
        
        for keyword in self.industry_keywords:
            if any(keyword in topic for topic in mapping.materiality_topics):
                related_industry.append(keyword)
        
        for keyword in self.sasb_issue_keywords:
            if any(keyword in topic for topic in mapping.materiality_topics):
                related_sasb.append(keyword)
        
        return {
            "industry_keywords": related_industry,
            "sasb_keywords": related_sasb
        }

    def get_mapping_statistics(self) -> Dict[str, Any]:
        """매핑 통계 정보 반환 (sasb-service 키워드 통계 포함)"""
        stats = {
            "total_sasb_codes": len(self.mapping_table),
            "total_materiality_topics": len(self.reverse_mapping),
            "total_industry_keywords": len(self.industry_keywords),
            "total_sasb_issue_keywords": len(self.sasb_issue_keywords),
            "category_distribution": {"E": 0, "S": 0, "G": 0}
        }
        
        for mapping in self.mapping_table.values():
            stats["category_distribution"][mapping.sasb_category] += 1
        
        return stats 