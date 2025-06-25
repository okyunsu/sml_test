import os
import re
import warnings
from typing import List, Dict, Any, Optional
import logging
import pandas as pd

from pdfminer.high_level import extract_text
from konlpy.tag import Okt
from sklearn.model_selection import train_test_split

from app.domain.model.tuning_request import TaskType
from app.domain.service.gri_data_service import GRIDataService

logger = logging.getLogger(__name__)

# PDF 처리 관련 경고 억제
warnings.filterwarnings("ignore", message=".*Cannot set gray.*color.*")
warnings.filterwarnings("ignore", message=".*invalid float value.*")

# pdfminer 로거 레벨 조정
logging.getLogger('pdfminer').setLevel(logging.ERROR)

class DataService:
    def __init__(self):
        self.okt = Okt()
        # GRI 서비스 초기화
        self.gri_service = GRIDataService()
        
        # 기본 ESG 키워드 (GRI로 확장 예정)
        self.esg_keywords = {
            "환경": ["환경", "기후", "탄소", "온실가스", "재생에너지", "친환경", "지속가능", "녹색"],
            "사회": ["사회", "임직원", "인권", "다양성", "안전", "보건", "지역사회", "사회공헌"],
            "지배구조": ["지배구조", "이사회", "투명성", "윤리", "컴플라이언스", "리스크", "감사"]
        }
        
        # GRI 기반 확장 키워드 (런타임에 로드)
        self.enhanced_keywords = None
        self.gri_mapping = None
    
    async def initialize_gri_keywords(self):
        """GRI 기반 키워드 초기화"""
        try:
            if self.gri_service.gri_standards:
                enhanced_mapping = await self.gri_service.create_enhanced_keyword_mapping()
                self.enhanced_keywords = enhanced_mapping["enhanced_keywords"]
                self.gri_mapping = enhanced_mapping["keyword_to_gri_mapping"]
                logger.info("✅ GRI 기반 키워드 초기화 완료")
            else:
                logger.info("ℹ️ GRI 데이터가 없어 기본 키워드 사용")
        except Exception as e:
            logger.warning(f"⚠️ GRI 키워드 초기화 실패, 기본 키워드 사용: {str(e)}")
    
    def get_active_keywords(self) -> Dict[str, List[str]]:
        """활성 키워드 반환 (GRI 확장 또는 기본)"""
        return self.enhanced_keywords if self.enhanced_keywords else self.esg_keywords
    
    def get_gri_standard_for_keyword(self, keyword: str) -> Optional[str]:
        """키워드에 해당하는 GRI 표준 반환"""
        if self.gri_mapping:
            return self.gri_mapping.get(keyword)
        return None
    
    async def extract_data_from_reports(
        self, 
        report_files: List[str], 
        task_type: TaskType
    ) -> pd.DataFrame:
        """ESG 보고서 또는 GRI 학습 데이터에서 데이터 추출"""
        try:
            # 기존 PDF 처리 로직
            all_data = []
            total_files = len(report_files)
            
            logger.info(f"📊 총 {total_files}개의 PDF 파일 처리 시작...")
            
            for idx, file_path in enumerate(report_files, 1):
                file_name = os.path.basename(file_path)
                logger.info(f"📄 [{idx}/{total_files}] 처리 중: {file_name}")
                
                # PDF 텍스트 추출
                text = await self._extract_text_from_pdf(file_path)
                
                if not text or len(text.strip()) < 100:
                    logger.warning(f"⚠️  [{idx}/{total_files}] {file_name}: 텍스트 추출 실패 또는 내용 부족")
                    continue
                
                logger.info(f"✅ [{idx}/{total_files}] {file_name}: 텍스트 추출 완료 ({len(text):,} 문자)")
                
                # 작업 타입에 따른 데이터 생성
                if task_type == TaskType.CLASSIFICATION:
                    data = await self._create_classification_data(text)
                elif task_type == TaskType.QUESTION_ANSWERING:
                    data = await self._create_qa_data(text)
                elif task_type == TaskType.SUMMARIZATION:
                    data = await self._create_summarization_data(text)
                else:
                    data = await self._create_generation_data(text)
                
                logger.info(f"🔄 [{idx}/{total_files}] {file_name}: {len(data)}개 훈련 샘플 생성")
                all_data.extend(data)
                
                # 진행률 계산
                progress = (idx / total_files) * 100
                logger.info(f"📈 전체 진행률: {progress:.1f}% ({idx}/{total_files} 완료)")
            
            df = pd.DataFrame(all_data)
            logger.info(f"🎉 데이터 추출 완료! 총 {len(df):,}개 훈련 샘플 생성")
            return df
            
        except Exception as e:
            logger.error(f"❌ 보고서 데이터 추출 중 오류: {str(e)}")
            raise ValueError(f"보고서 데이터 추출 중 오류가 발생했습니다: {str(e)}")
    
    async def _load_gri_learning_dataset(self, dataset_path: str, task_type: TaskType) -> pd.DataFrame:
        """GRI 학습 데이터셋 로드 및 Hugging Face 형식으로 변환"""
        try:
            logger.info(f"📖 GRI 학습 데이터셋 로드 중: {dataset_path}")
            
            # CSV 파일 로드
            df = pd.read_csv(dataset_path, encoding='utf-8')
            logger.info(f"📊 원본 데이터셋 크기: {len(df)} 샘플")
            
            # Hugging Face 형식으로 변환
            if task_type == TaskType.TEXT_GENERATION:
                # 텍스트 생성용 형식: input_text -> target_text
                hf_data = []
                for _, row in df.iterrows():
                    hf_data.append({
                        "text": f"질문: {row['input_text']}\n답변: {row['target_text']}"
                    })
                
                hf_df = pd.DataFrame(hf_data)
                logger.info(f"✅ GRI 텍스트 생성 데이터셋 변환 완료: {len(hf_df)} 샘플")
                return hf_df
                
            elif task_type == TaskType.QUESTION_ANSWERING:
                # 질의응답용 형식
                hf_data = []
                for _, row in df.iterrows():
                    hf_data.append({
                        "question": row['input_text'],
                        "context": row['target_text'],
                        "answers": {
                            "text": [row['target_text'][:200]],  # 답변 일부
                            "answer_start": [0]
                        }
                    })
                
                hf_df = pd.DataFrame(hf_data)
                logger.info(f"✅ GRI 질의응답 데이터셋 변환 완료: {len(hf_df)} 샘플")
                return hf_df
                
            else:
                # 기본적으로 텍스트 생성으로 처리
                return await self._load_gri_learning_dataset(dataset_path, TaskType.TEXT_GENERATION)
                
        except Exception as e:
            logger.error(f"❌ GRI 학습 데이터셋 로드 실패: {str(e)}")
            raise ValueError(f"GRI 학습 데이터셋 로드 실패: {str(e)}")
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """PDF에서 텍스트 추출"""
        try:
            # 표준 출력/에러를 임시로 억제하여 색상 관련 경고 숨기기
            import sys
            from io import StringIO
            
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            try:
                text = extract_text(file_path)
            finally:
                # 표준 에러 복원
                sys.stderr = old_stderr
            
            # 텍스트 정리
            text = re.sub(r'\s+', ' ', text)  # 여러 공백을 하나로
            text = re.sub(r'\n+', '\n', text)  # 여러 줄바꿈을 하나로
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {str(e)}")
            # 빈 텍스트 대신 기본 ESG 텍스트 반환하여 파인튜닝이 계속 진행되도록 함
            return "ESG 보고서 텍스트 추출에 실패했습니다. 환경, 사회, 지배구조 관련 내용입니다."
    
    async def _create_classification_data(self, text: str) -> List[Dict[str, Any]]:
        """분류 작업용 데이터 생성"""
        data = []
        
        # 문장 단위로 분할
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:  # 최소 길이 줄임
                continue
            
            # GRI PDF는 모든 내용이 ESG 관련이므로 모두 1로 설정
            data.append({
                "text": sentence.strip(),
                "labels": 1  # 모든 GRI 내용은 ESG 관련
            })
        
        return data[:100]  # 최대 100개 샘플로 제한
    
    async def _create_qa_data(self, text: str) -> List[Dict[str, Any]]:
        """질의응답 작업용 데이터 생성"""
        data = []
        
        # 문단 단위로 분할
        paragraphs = self._split_into_paragraphs(text)
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) < 50:  # 최소 길이 줄임
                continue
            
            # GRI PDF는 모든 내용이 ESG 관련이므로 필터 제거
            # 질문-답변 쌍 생성
            qa_pairs = self._generate_qa_pairs(paragraph)
            
            for question, answer, start_pos in qa_pairs:
                data.append({
                    "question": question,
                    "context": paragraph,
                    "answers": {
                        "text": [answer],
                        "answer_start": [start_pos]
                    }
                })
        
        return data[:50]  # 최대 50개 샘플로 제한
    
    async def _create_summarization_data(self, text: str) -> List[Dict[str, Any]]:
        """요약 작업용 데이터 생성"""
        data = []
        
        # 섹션 단위로 분할
        sections = self._split_into_sections(text)
        
        for section in sections:
            if len(section.strip()) < 100:  # 최소 길이 줄임
                continue
            
            # GRI PDF는 모든 내용이 ESG 관련이므로 필터 제거
            # 요약 생성 (첫 번째 문장을 요약으로 사용)
            sentences = self._split_into_sentences(section)
            if len(sentences) > 1:
                summary = sentences[0]
                content = " ".join(sentences[1:])
                
                data.append({
                    "text": content,
                    "summary": summary
                })
        
        return data[:30]  # 최대 30개 샘플로 제한
    
    async def _create_generation_data(self, text: str) -> List[Dict[str, Any]]:
        """텍스트 생성 작업용 데이터 생성"""
        data = []
        
        # 문단 단위로 분할
        paragraphs = self._split_into_paragraphs(text)
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) < 50:  # 최소 길이 줄임
                continue
            
            # GRI PDF는 모든 내용이 ESG 관련이므로 필터 제거
            # 프롬프트-응답 쌍 생성
            prompts = self._generate_prompts(paragraph)
            
            for prompt in prompts:
                # 텍스트 길이 제한 (토큰 제한 고려)
                combined_text = f"{prompt} {paragraph}"
                if len(combined_text) > 1000:
                    combined_text = combined_text[:1000] + "..."
                
                data.append({
                    "text": combined_text
                })
        
        return data
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분할"""
        # 한국어 문장 분할
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """텍스트를 문단 단위로 분할"""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_into_sections(self, text: str) -> List[str]:
        """텍스트를 섹션 단위로 분할"""
        # 제목 패턴으로 섹션 분할
        sections = re.split(r'\n(?=[0-9]+\.|[가-힣]+\s*[0-9]*\.)', text)
        return [s.strip() for s in sections if s.strip()]
    
    def _is_esg_related(self, text: str) -> bool:
        """텍스트가 ESG 관련인지 판단 (GRI 기반 향상)"""
        text_lower = text.lower()
        
        # 활성 키워드 사용 (GRI 확장 또는 기본)
        active_keywords = self.get_active_keywords()
        
        # ESG 키워드 검사
        for category, keywords in active_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # GRI 표준 정보 추가 (있는 경우)
                    gri_standard = self.get_gri_standard_for_keyword(keyword)
                    if gri_standard:
                        logger.debug(f"키워드 '{keyword}' -> GRI: {gri_standard}")
                    return True
        
        return False
    
    def _generate_qa_pairs(self, paragraph: str) -> List[tuple]:
        """문단에서 질문-답변 쌍 생성"""
        qa_pairs = []
        
        # 간단한 패턴 기반 QA 생성
        sentences = self._split_into_sentences(paragraph)
        
        for i, sentence in enumerate(sentences):
            # 수치가 포함된 문장에서 질문 생성
            numbers = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', sentence)
            if numbers:
                for num in numbers:
                    question = f"해당 수치는 얼마입니까?"
                    answer = num
                    start_pos = sentence.find(num)
                    if start_pos != -1:
                        qa_pairs.append((question, answer, start_pos))
            
            # 키워드 기반 질문 생성
            for category, keywords in self.esg_keywords.items():
                for keyword in keywords:
                    if keyword in sentence:
                        question = f"{category}에 대한 내용은 무엇입니까?"
                        answer = sentence
                        qa_pairs.append((question, answer, 0))
                        break
        
        return qa_pairs[:3]  # 최대 3개까지
    
    def _generate_prompts(self, paragraph: str) -> List[str]:
        """문단에 대한 프롬프트 생성"""
        prompts = [
            "다음 ESG 내용에 대해 설명해주세요:",
            "이 ESG 보고서 내용을 요약하면:",
            "ESG 관점에서 다음 내용의 의미는:",
            "지속가능경영 측면에서 다음 내용은:"
        ]
        
        return prompts[:2]  # 최대 2개까지
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 특수문자 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def create_custom_dataset(
        self, 
        texts: List[str], 
        labels: Optional[List[int]] = None,
        task_type: TaskType = TaskType.CLASSIFICATION
    ) -> pd.DataFrame:
        """커스텀 데이터셋 생성"""
        if task_type == TaskType.CLASSIFICATION and labels is None:
            raise ValueError("분류 작업에는 레이블이 필요합니다.")
        
        data = []
        for i, text in enumerate(texts):
            processed_text = self.preprocess_text(text)
            
            if task_type == TaskType.CLASSIFICATION:
                data.append({
                    "text": processed_text,
                    "labels": labels[i]  # labels 컬럼만 사용
                })
            else:
                data.append({
                    "text": processed_text
                })
        
        return pd.DataFrame(data) 