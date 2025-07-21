import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from ..model.materiality_dto import MaterialityAssessment, MaterialityTopic
from .materiality_mapping_service import MaterialityMappingService
from .materiality_parsing_service import MaterialityParsingService

logger = logging.getLogger(__name__)

class MaterialityFileService:
    """중대성 평가 파일 관리 서비스"""
    
    def __init__(self):
        self.mapping_service = MaterialityMappingService()
        self.parsing_service = MaterialityParsingService()
        self.base_path = Path(__file__).parent.parent.parent / "materiality"
        
        # MVP 지원 기업 목록
        self.supported_companies = {
            "두산퓨얼셀": "doosan.txt",
            "LS ELECTRIC": "ls.txt"
        }
    
    def get_company_file_path(self, company_name: str) -> Optional[Path]:
        """기업명에 해당하는 파일 경로 반환"""
        if company_name not in self.supported_companies:
            return None
        
        filename = self.supported_companies[company_name]
        file_path = self.base_path / filename
        
        if not file_path.exists():
            logger.warning(f"파일이 존재하지 않음: {file_path}")
            return None
        
        return file_path
    
    def load_company_assessment(self, company_name: str, year: int = 2024) -> Optional[MaterialityAssessment]:
        """기업의 중대성 평가 데이터 로드"""
        try:
            file_path = self.get_company_file_path(company_name)
            if not file_path:
                logger.error(f"지원하지 않는 기업: {company_name}")
                return None
            
            # 파일 내용 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # 파싱 서비스를 통해 데이터 처리
            assessment = self.parsing_service.parse_txt_content(
                file_content, 
                company_name, 
                year, 
                "simple_list"
            )
            
            logger.info(f"중대성 평가 데이터 로드 성공: {company_name} {year}년")
            return assessment
            
        except Exception as e:
            logger.error(f"중대성 평가 데이터 로드 실패: {str(e)}")
            return None
    
    def get_supported_companies(self) -> List[str]:
        """지원 기업 목록 반환"""
        return list(self.supported_companies.keys())
    
    def save_company_assessment(self, company_name: str, content: str) -> bool:
        """기업의 중대성 평가 데이터 저장 (향후 확장용)"""
        try:
            # 새로운 기업 지원을 위한 확장 가능한 구조
            if company_name not in self.supported_companies:
                # 파일명 생성 (기업명을 영문으로 변환하는 로직 필요)
                filename = f"{company_name.lower().replace(' ', '_')}.txt"
                self.supported_companies[company_name] = filename
            
            file_path = self.get_company_file_path(company_name)
            if not file_path:
                filename = self.supported_companies[company_name]
                file_path = self.base_path / filename
            
            # 디렉토리가 존재하지 않으면 생성
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"중대성 평가 데이터 저장 성공: {company_name}")
            return True
            
        except Exception as e:
            logger.error(f"중대성 평가 데이터 저장 실패: {str(e)}")
            return False
    
    def get_file_info(self, company_name: str) -> Optional[Dict]:
        """파일 정보 반환"""
        file_path = self.get_company_file_path(company_name)
        if not file_path:
            return None
        
        try:
            stat = file_path.stat()
            return {
                "company_name": company_name,
                "filename": file_path.name,
                "size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "exists": True
            }
        except Exception as e:
            logger.error(f"파일 정보 조회 실패: {str(e)}")
            return None
    
    def validate_file_exists(self, company_name: str) -> bool:
        """파일 존재 여부 확인"""
        file_path = self.get_company_file_path(company_name)
        return file_path is not None and file_path.exists()
    
    def save_assessment_to_file(self, assessment: MaterialityAssessment) -> str:
        """중대성 평가 객체를 파일로 저장"""
        try:
            # 저장 경로 생성
            save_dir = self.base_path / "generated_assessments"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일명 생성
            filename = f"{assessment.company_name}_{assessment.year}_{assessment.assessment_id}.txt"
            file_path = save_dir / filename
            
            # 파일 내용 생성
            content_lines = [
                f"# {assessment.company_name} {assessment.year}년 중대성 평가",
                f"# 생성일시: {assessment.upload_date.strftime('%Y-%m-%d %H:%M:%S')}",
                f"# 평가 ID: {assessment.assessment_id}",
                ""
            ]
            
            # 생성 메타데이터 추가
            if hasattr(assessment, 'generation_metadata'):
                metadata = getattr(assessment, 'generation_metadata', {})
                if metadata:
                    content_lines.extend([
                        "# 생성 메타데이터:",
                        f"# - 생성 방법: {metadata.get('generation_method', 'unknown')}",
                        f"# - 생성 신뢰도: {metadata.get('generation_confidence', 'unknown')}",
                        f"# - 기준 평가 연도: {metadata.get('base_assessment_year', 'unknown')}",
                        f"# - 분석 기사 수: {metadata.get('total_news_articles', 'unknown')}",
                        f"# - 신규 이슈 추가: {metadata.get('new_issues_added', 'unknown')}개",
                        f"# - 수정된 토픽: {metadata.get('topics_modified', 'unknown')}개",
                        ""
                    ])
            
            # 토픽 목록 추가 (우선순위 순)
            content_lines.append("# 중대성 평가 토픽 (우선순위 순):")
            sorted_topics = sorted(assessment.topics, key=lambda x: x.priority)
            
            for topic in sorted_topics:
                sasb_info = ""
                if topic.sasb_mapping:
                    sasb_code = getattr(topic.sasb_mapping, 'sasb_code', None)
                    if sasb_code:
                        sasb_info = f" [SASB: {sasb_code}]"
                
                metadata_info = ""
                if hasattr(topic, 'metadata'):
                    metadata = getattr(topic, 'metadata', {})
                    if metadata and 'change_type' in metadata:
                        metadata_info = f" ({metadata['change_type']})"
                
                content_lines.append(f"{topic.priority}. {topic.topic_name}{sasb_info}{metadata_info}")
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))
            
            logger.info(f"중대성 평가 파일 저장 성공: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"중대성 평가 파일 저장 실패: {str(e)}")
            raise
    
    def load_generated_assessment(self, company_name: str, year: int, assessment_id: str) -> Optional[MaterialityAssessment]:
        """생성된 중대성 평가 파일 로드"""
        try:
            save_dir = self.base_path / "generated_assessments"
            filename = f"{company_name}_{year}_{assessment_id}.txt"
            file_path = save_dir / filename
            
            if not file_path.exists():
                logger.warning(f"생성된 평가 파일이 존재하지 않음: {file_path}")
                return None
            
            # 파일 내용 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 간단한 파싱 (주석 제거 후 토픽 추출)
            lines = content.split('\n')
            topics = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # "1. 토픽명 [SASB: 코드] (변화타입)" 형태 파싱
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        priority = int(parts[0].strip())
                        topic_info = parts[1].strip()
                        
                        # 토픽명 추출
                        topic_name = topic_info.split('[')[0].strip()
                        
                        topic = MaterialityTopic(
                            topic_name=topic_name,
                            priority=priority,
                            sasb_mapping=None  # 필요시 복원 로직 추가
                        )
                        topics.append(topic)
            
            # 평가 객체 생성
            assessment = MaterialityAssessment(
                assessment_id=assessment_id,
                company_name=company_name,
                year=year,
                topics=topics,
                upload_date=datetime.now()
            )
            
            logger.info(f"생성된 중대성 평가 로드 성공: {company_name} {year}년")
            return assessment
            
        except Exception as e:
            logger.error(f"생성된 중대성 평가 로드 실패: {str(e)}")
            return None 