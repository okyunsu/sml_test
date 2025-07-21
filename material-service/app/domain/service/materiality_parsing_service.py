from typing import List, Dict, Optional, IO
import io
import logging
from datetime import datetime
from ..model.materiality_dto import MaterialityTopic, MaterialityAssessment
from .materiality_mapping_service import MaterialityMappingService

logger = logging.getLogger(__name__)

class MaterialityParsingService:
    """중대성 평가 파일 파싱 서비스"""
    
    def __init__(self):
        self.mapping_service = MaterialityMappingService()
    
    def parse_txt_content(
        self, 
        file_content: str, 
        company_name: str, 
        year: int,
        file_format: str = "simple_list"
    ) -> MaterialityAssessment:
        """
        TXT 파일 내용을 파싱하여 중대성 평가 데이터로 변환
        
        지원 형식:
        1. simple_list: 줄별로 토픽명만 나열 (우선순위는 순서대로)
        2. priority_format: "토픽명:우선순위" 형태
        """
        try:
            if file_format == "simple_list":
                topics = self._parse_simple_list(file_content, company_name, year)
            elif file_format == "priority_format":
                topics = self._parse_priority_format(file_content, company_name, year)
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {file_format}")
            
            # SASB 자동 매핑 적용
            mapped_topics = self.mapping_service.auto_map_topics(topics)
            
            # 평가 결과 생성
            assessment = MaterialityAssessment(
                assessment_id=f"{company_name}_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                company_name=company_name,
                year=year,
                topics=mapped_topics,
                upload_date=datetime.now()
            )
            
            logger.info(f"파싱 완료: {company_name} {year}년, {len(mapped_topics)}개 토픽")
            return assessment
            
        except Exception as e:
            logger.error(f"파일 파싱 실패: {str(e)}")
            raise
    
    def _parse_simple_list(self, content: str, company_name: str, year: int) -> List[MaterialityTopic]:
        """간단한 목록 형태 파싱 (줄별로 토픽명, 우선순위는 순서대로)"""
        topics = []
        lines = content.strip().split('\n')
        
        for priority, line in enumerate(lines, 1):
            topic_name = line.strip()
            if topic_name:  # 빈 줄이 아닌 경우만 처리
                topic = MaterialityTopic(
                    topic_name=topic_name,
                    priority=priority,
                    year=year,
                    company_name=company_name,
                    sasb_mapping=None
                )
                topics.append(topic)
        
        return topics
    
    def _parse_priority_format(self, content: str, company_name: str, year: int) -> List[MaterialityTopic]:
        """우선순위 형태 파싱 (토픽명:우선순위)"""
        topics = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    topic_name = parts[0].strip()
                    try:
                        priority = int(parts[1].strip())
                        topic = MaterialityTopic(
                            topic_name=topic_name,
                            priority=priority,
                            year=year,
                            company_name=company_name,
                            sasb_mapping=None
                        )
                        topics.append(topic)
                    except ValueError:
                        logger.warning(f"우선순위 파싱 실패: '{line}'")
        
        # 우선순위 순으로 정렬
        topics.sort(key=lambda x: x.priority)
        return topics 