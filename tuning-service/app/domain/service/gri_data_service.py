import os
import re
import json
import logging
import glob
from typing import Dict, List, Tuple, Optional, Any
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import PyPDF2
from pathlib import Path

logger = logging.getLogger(__name__)

class GRIDataService:
    """GRI Standard PDF를 활용한 포괄적 ESG 키워드 매핑 서비스"""
    
    def __init__(self):
        self.sbert_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        self.gri_standards = {}
        self.gri_keywords = {}
        self.gri_embeddings = {}
        self.gri_folder = "data/gri"
        self.training_folder = "data/training"
        
        # 훈련 폴더 생성
        os.makedirs(self.training_folder, exist_ok=True)
        
    async def create_gri_standards_learning_dataset(self) -> Dict[str, Any]:
        """GRI 기준 PDF 파일들을 읽어서 실제 GRI 기준을 학습할 수 있는 데이터셋 생성"""
        try:
            logger.info("🔍 GRI 기준 학습 데이터셋 생성 시작...")
            
            # GRI PDF 파일들 찾기
            gri_files = self._find_gri_files()
            if not gri_files:
                raise ValueError("GRI PDF 파일을 찾을 수 없습니다.")
            
            logger.info(f"📁 발견된 GRI 파일 수: {len(gri_files)}")
            
            # 각 PDF 파일에서 실제 내용 추출
            training_data = []
            processed_count = 0
            
            for file_path in gri_files[:5]:  # 테스트용으로 처음 5개만
                try:
                    logger.info(f"📖 처리 중: {os.path.basename(file_path)}")
                    
                    # PDF 내용 추출
                    pdf_content = self._extract_pdf_content(file_path)
                    if not pdf_content or len(pdf_content.strip()) < 100:
                        logger.warning(f"⚠️ PDF 내용이 부족합니다: {file_path}")
                        continue
                    
                    # GRI 정보 파싱
                    gri_info = self._parse_gri_info_from_filename(file_path)
                    
                    # 실제 GRI 기준 학습을 위한 다양한 훈련 데이터 생성
                    file_training_data = self._create_gri_learning_samples(
                        pdf_content, gri_info, file_path
                    )
                    
                    training_data.extend(file_training_data)
                    processed_count += 1
                    
                    logger.info(f"✅ 처리 완료: {os.path.basename(file_path)} ({len(file_training_data)}개 샘플 생성)")
                    
                except Exception as e:
                    logger.error(f"❌ 파일 처리 실패 {file_path}: {str(e)}")
                    continue
            
            if not training_data:
                raise ValueError("유효한 GRI 학습 데이터를 생성할 수 없습니다.")
            
            # 데이터프레임 생성 및 저장
            df = pd.DataFrame(training_data)
            output_path = os.path.join(self.training_folder, "gri_standards_learning_dataset.csv")
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            result = {
                "success": True,
                "dataset_path": output_path,
                "total_samples": len(training_data),
                "processed_files": processed_count,
                "total_files": len(gri_files),
                "sample_data": training_data[:3] if training_data else []
            }
            
            logger.info(f"🎉 GRI 기준 학습 데이터셋 생성 완료!")
            logger.info(f"📊 총 {len(training_data)}개 학습 샘플 생성")
            logger.info(f"💾 저장 경로: {output_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ GRI 기준 학습 데이터셋 생성 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "dataset_path": None,
                "total_samples": 0
            }
    
    def _extract_pdf_content(self, file_path: str) -> str:
        """PDF 파일에서 실제 텍스트 내용 추출"""
        try:
            content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 처음 10페이지만 추출 (너무 길어지지 않도록)
                max_pages = min(10, len(pdf_reader.pages))
                
                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
                
                # 텍스트 정리
                content = self._clean_pdf_text(content)
                
            return content
            
        except Exception as e:
            logger.error(f"PDF 내용 추출 실패 {file_path}: {str(e)}")
            return ""
    
    def _clean_pdf_text(self, text: str) -> str:
        """PDF에서 추출한 텍스트 정리"""
        if not text:
            return ""
        
        # 기본 정리
        text = text.replace('\n\n', '\n')
        text = text.replace('\t', ' ')
        text = ' '.join(text.split())  # 여러 공백을 하나로
        
        # 너무 긴 텍스트는 자르기 (토큰 제한 고려)
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        return text.strip()
    
    def _create_gri_learning_samples(self, pdf_content: str, gri_info: Dict, file_path: str) -> List[Dict]:
        """실제 GRI 기준을 학습할 수 있는 다양한 훈련 샘플 생성"""
        samples = []
        
        gri_number = gri_info.get('number', 'Unknown')
        gri_title = gri_info.get('title', 'Unknown')
        category = gri_info.get('category', 'Unknown')
        
        # 1. GRI 기준 설명 학습
        samples.append({
            "input_text": f"GRI {gri_number} {gri_title}에 대해 자세히 설명해주세요.",
            "target_text": f"GRI {gri_number} {gri_title}는 {category} 분야의 지속가능성 보고 표준입니다.\n\n{pdf_content[:1000]}",
            "task_type": "gri_explanation",
            "gri_standard": gri_number,
            "gri_title": gri_title,
            "category": category,
            "source_file": os.path.basename(file_path)
        })
        
        # 2. GRI 기준 요구사항 학습
        samples.append({
            "input_text": f"GRI {gri_number}의 주요 요구사항과 공시 항목은 무엇인가요?",
            "target_text": f"GRI {gri_number} {gri_title}의 주요 요구사항:\n\n{pdf_content[500:1500]}",
            "task_type": "gri_requirements",
            "gri_standard": gri_number,
            "gri_title": gri_title,
            "category": category,
            "source_file": os.path.basename(file_path)
        })
        
        # 3. GRI 기준 적용 가이드 학습
        samples.append({
            "input_text": f"기업이 GRI {gri_number}를 적용할 때 고려해야 할 사항은 무엇인가요?",
            "target_text": f"GRI {gri_number} {gri_title} 적용 시 고려사항:\n\n{pdf_content[1000:2000]}",
            "task_type": "gri_guidance",
            "gri_standard": gri_number,
            "gri_title": gri_title,
            "category": category,
            "source_file": os.path.basename(file_path)
        })
        
        # 4. 카테고리 분류 학습
        samples.append({
            "input_text": f"GRI {gri_number} {gri_title}는 ESG의 어떤 영역에 해당하나요?",
            "target_text": f"GRI {gri_number} {gri_title}는 {category} 영역에 해당합니다. 이는 지속가능성 보고에서 {category.lower()} 성과를 측정하고 보고하는 데 사용됩니다.",
            "task_type": "category_classification",
            "gri_standard": gri_number,
            "gri_title": gri_title,
            "category": category,
            "source_file": os.path.basename(file_path)
        })
        
        # 5. 실제 내용 기반 질의응답 학습
        if len(pdf_content) > 500:
            content_snippet = pdf_content[200:800]
            samples.append({
                "input_text": f"다음 GRI {gri_number} 내용을 바탕으로 핵심 포인트를 설명해주세요:\n\n{content_snippet[:300]}",
                "target_text": f"해당 내용의 핵심 포인트는 다음과 같습니다:\n\n{content_snippet[300:]}",
                "task_type": "content_analysis",
                "gri_standard": gri_number,
                "gri_title": gri_title,
                "category": category,
                "source_file": os.path.basename(file_path)
            })
        
        return samples
    
    def _extract_gri_info_from_filename(self, filename: str) -> Dict[str, str]:
        """파일명에서 GRI 정보 추출"""
        gri_info = {
            "number": "Unknown",
            "title": "Unknown", 
            "year": "Unknown",
            "category": "Unknown"
        }
        
        try:
            if "GRI " in filename:
                parts = filename.split("GRI ")[1]
                
                if "_" in parts:
                    number_part = parts.split("_")[0].strip()
                    title_part = parts.split("_")[1].split(".pdf")[0].strip()
                    
                    # 연도 추출
                    year_match = re.search(r'\d{4}', title_part)
                    if year_match:
                        gri_info["year"] = year_match.group()
                        title_part = re.sub(r'\d{4}', '', title_part).strip()
                    
                    gri_info["number"] = number_part
                    gri_info["title"] = title_part
                    gri_info["category"] = self._categorize_gri_standard_by_number(number_part)
                    
        except Exception as e:
            logger.warning(f"파일명 파싱 실패: {filename} - {str(e)}")
        
        return gri_info
    
    def _categorize_gri_standard_by_number(self, gri_number: str) -> str:
        """GRI 표준 번호를 카테고리로 분류"""
        try:
            num_match = re.search(r'\d+', gri_number)
            if num_match:
                num = int(num_match.group())
                
                if num <= 100:
                    return "Foundation & General"
                elif num <= 200:
                    return "Economic"
                elif num <= 300:
                    return "Environmental"
                else:
                    return "Social"
        except:
            pass
        
        # 키워드 기반 분류
        gri_lower = gri_number.lower()
        if any(word in gri_lower for word in ['foundation', 'general', 'material']):
            return "Foundation & General"
        elif any(word in gri_lower for word in ['economic', 'performance', 'market', 'procurement']):
            return "Economic"
        elif any(word in gri_lower for word in ['environmental', 'emission', 'energy', 'water', 'waste', 'biodiversity']):
            return "Environmental"
        elif any(word in gri_lower for word in ['social', 'employment', 'training', 'diversity', 'health', 'safety']):
            return "Social"
        
        return "Unknown"
    
    def _split_gri_content_into_sections(self, content) -> Dict[str, str]:
        """GRI 기준서 내용을 의미있는 섹션으로 분할"""
        if isinstance(content, dict):
            return content
        
        text = str(content)
        sections = {}
        
        # GRI 문서의 일반적인 섹션 구조
        section_patterns = [
            r'(?i)(disclosure|requirement|guidance|management approach|reporting guidance)',
            r'(?i)(background|rationale|compilation requirements)',
            r'(?i)(definitions|glossary|references)'
        ]
        
        # 패턴 기반 섹션 분할
        current_section = "Main Content"
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 섹션 헤더 감지
            section_found = False
            for pattern in section_patterns:
                if re.search(pattern, line):
                    # 이전 섹션 저장
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # 새 섹션 시작
                    current_section = line[:50] + "..." if len(line) > 50 else line
                    current_content = []
                    section_found = True
                    break
            
            if not section_found:
                current_content.append(line)
        
        # 마지막 섹션 저장
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # 섹션이 없으면 전체를 하나의 섹션으로
        if not sections:
            sections["Main Content"] = text
        
        return sections
    
    def _generate_training_data_from_sections(self, sections: Dict[str, str], gri_number: str, 
                                            gri_title: str, category: str, file_name: str) -> List[Dict]:
        """섹션별로 다양한 형태의 학습 데이터 생성"""
        training_data = []
        
        for section_title, section_content in sections.items():
            if len(section_content) < 100:  # 너무 짧은 섹션 제외
                continue
            
            # 1. GRI 표준 설명 학습
            training_data.append({
                "input_text": f"GRI {gri_number}에 대해 설명해주세요.",
                "target_text": f"GRI {gri_number} ({gri_title})는 {category} 카테고리의 표준입니다. {section_content[:300]}...",
                "gri_standard": gri_number,
                "gri_title": gri_title,
                "category": category,
                "section": section_title,
                "task_type": "standard_explanation",
                "source_file": file_name
            })
            
            # 2. GRI 요구사항 학습
            if "requirement" in section_title.lower() or "disclosure" in section_title.lower():
                training_data.append({
                    "input_text": f"GRI {gri_number}의 공시 요구사항은 무엇인가요?",
                    "target_text": f"GRI {gri_number}의 공시 요구사항: {section_content[:400]}...",
                    "gri_standard": gri_number,
                    "gri_title": gri_title,
                    "category": category,
                    "section": section_title,
                    "task_type": "requirement_explanation",
                    "source_file": file_name
                })
            
            # 3. GRI 가이던스 학습
            if "guidance" in section_title.lower() or "recommendation" in section_title.lower():
                training_data.append({
                    "input_text": f"GRI {gri_number} 적용 시 고려사항은 무엇인가요?",
                    "target_text": f"GRI {gri_number} 적용 가이던스: {section_content[:400]}...",
                    "gri_standard": gri_number,
                    "gri_title": gri_title,
                    "category": category,
                    "section": section_title,
                    "task_type": "guidance",
                    "source_file": file_name
                })
            
            # 4. 카테고리별 분류 학습
            training_data.append({
                "input_text": f"다음 내용이 어떤 GRI 카테고리에 속하는지 분류해주세요: {section_content[:200]}...",
                "target_text": f"이 내용은 {category} 카테고리의 GRI {gri_number} ({gri_title}) 표준에 속합니다.",
                "gri_standard": gri_number,
                "gri_title": gri_title,
                "category": category,
                "section": section_title,
                "task_type": "category_classification",
                "source_file": file_name
            })
            
            # 5. 키워드 기반 GRI 매칭 학습
            keywords = self._extract_key_terms_from_content(section_content)
            if keywords:
                keyword_text = ", ".join(keywords[:5])
                training_data.append({
                    "input_text": f"'{keyword_text}' 키워드와 관련된 GRI 표준은 무엇인가요?",
                    "target_text": f"'{keyword_text}' 키워드는 GRI {gri_number} ({gri_title}) 표준과 관련됩니다. {section_content[:200]}...",
                    "gri_standard": gri_number,
                    "gri_title": gri_title,
                    "category": category,
                    "section": section_title,
                    "task_type": "keyword_matching",
                    "keywords": keyword_text,
                    "source_file": file_name
                })
        
        return training_data
    
    def _extract_key_terms_from_content(self, content: str) -> List[str]:
        """내용에서 핵심 용어 추출"""
        gri_terms = [
            # Environmental
            'emission', 'emissions', 'greenhouse gas', 'carbon', 'energy', 'renewable',
            'water', 'waste', 'biodiversity', 'materials', 'pollution', 'climate',
            
            # Social  
            'employment', 'training', 'education', 'diversity', 'health', 'safety',
            'community', 'human rights', 'labor', 'discrimination', 'child labor',
            
            # Economic
            'economic performance', 'market presence', 'procurement', 'anti-corruption',
            'tax', 'indirect economic', 'supply chain',
            
            # Governance
            'governance', 'ethics', 'compliance', 'risk management', 'transparency',
            'stakeholder', 'materiality', 'disclosure'
        ]
        
        content_lower = content.lower()
        found_terms = []
        
        for term in gri_terms:
            if term in content_lower:
                count = content_lower.count(term)
                if count >= 2:  # 최소 2번 이상 등장
                    found_terms.append((term, count))
        
        # 빈도순으로 정렬
        found_terms.sort(key=lambda x: x[1], reverse=True)
        
        return [term[0] for term in found_terms[:10]]
    
    def _generate_dataset_statistics(self, df: pd.DataFrame, processed_count: int, total_files: int) -> Dict:
        """데이터셋 통계 정보 생성"""
        category_stats = df['category'].value_counts().to_dict()
        gri_stats = df['gri_standard'].value_counts().to_dict()
        task_stats = df['task_type'].value_counts().to_dict()
        
        return {
            "unique_gri_standards": df['gri_standard'].nunique(),
            "processed_files": processed_count,
            "available_gri_pdfs": total_files,
            "category_distribution": category_stats,
            "gri_distribution": dict(list(gri_stats.items())[:10]),  # 상위 10개만
            "task_type_distribution": task_stats
        }
    
    async def list_gri_models(self, models_dir: str = "models") -> Dict:
        """GRI 표준 학습 모델 목록 조회"""
        try:
            if not os.path.exists(models_dir):
                return {
                    "success": True,
                    "message": "아직 훈련된 GRI 모델이 없습니다",
                    "models": []
                }
            
            # GRI 관련 모델 찾기
            model_folders = [d for d in os.listdir(models_dir) 
                            if os.path.isdir(os.path.join(models_dir, d)) and 'gri' in d.lower()]
            
            models_info = []
            for model_folder in model_folders:
                model_path = os.path.join(models_dir, model_folder)
                
                model_info = {
                    "model_name": model_folder,
                    "model_path": model_path,
                    "created_date": "Unknown",
                    "model_size": "Unknown",
                    "tuning_type": "GRI Standards Learning"
                }
                
                # 모델 크기 계산
                try:
                    total_size = 0
                    for root, dirs, files in os.walk(model_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                    model_info["model_size"] = f"{total_size / (1024*1024):.1f} MB"
                except:
                    pass
                
                models_info.append(model_info)
            
            return {
                "success": True,
                "message": f"총 {len(models_info)}개의 GRI 학습 모델 발견",
                "models": models_info,
                "usage_note": "이 모델들은 GRI 표준을 이해하고 기업 보고서를 GRI 기준에 따라 분석할 수 있습니다"
            }
            
        except Exception as e:
            logger.error(f"❌ 모델 목록 조회 실패: {str(e)}")
            raise

    async def process_gri_pdf(self, gri_pdf_path: str) -> Dict:
        """GRI Standard PDF를 파싱하여 표준 데이터 추출"""
        try:
            logger.info(f"📄 GRI Standard PDF 처리 시작: {gri_pdf_path}")
            
            # PDF 텍스트 추출
            text = extract_text(gri_pdf_path)
            
            # GRI 표준별 섹션 분할
            gri_sections = self._extract_gri_sections(text)
            
            # 각 GRI 표준별 키워드 및 설명 추출
            for gri_code, content in gri_sections.items():
                keywords = self._extract_keywords_from_gri_section(content)
                description = self._extract_description_from_gri_section(content)
                
                self.gri_standards[gri_code] = {
                    "keywords": keywords,
                    "description": description,
                    "content": content[:1000]  # 처음 1000자만 저장
                }
                
                # 임베딩 생성
                self.gri_embeddings[gri_code] = self.sbert_model.encode(
                    f"{description} {' '.join(keywords)}"
                )
            
            logger.info(f"✅ GRI Standard 처리 완료: {len(self.gri_standards)}개 표준 추출")
            return self.gri_standards
            
        except Exception as e:
            logger.error(f"❌ GRI PDF 처리 실패: {str(e)}")
            raise
    
    def _extract_gri_sections(self, text: str) -> Dict[str, str]:
        """GRI 표준별 섹션 추출"""
        sections = {}
        
        # GRI 표준 패턴 (예: GRI 302: Energy, GRI 305: Emissions 등)
        gri_pattern = r'GRI\s+(\d+):\s*([^.\n]+)'
        matches = re.finditer(gri_pattern, text, re.IGNORECASE)
        
        for match in matches:
            gri_number = match.group(1)
            gri_title = match.group(2).strip()
            gri_code = f"GRI {gri_number}: {gri_title}"
            
            # 해당 섹션의 내용 추출 (다음 GRI까지)
            start_pos = match.start()
            next_match = re.search(r'GRI\s+\d+:', text[start_pos + 100:], re.IGNORECASE)
            
            if next_match:
                end_pos = start_pos + 100 + next_match.start()
                section_content = text[start_pos:end_pos]
            else:
                section_content = text[start_pos:start_pos + 2000]  # 최대 2000자
            
            sections[gri_code] = section_content
        
        return sections
    
    def _extract_keywords_from_gri_section(self, content: str) -> List[str]:
        """GRI 섹션에서 핵심 키워드 추출"""
        # TF-IDF를 사용한 키워드 추출
        vectorizer = TfidfVectorizer(
            max_features=20,
            stop_words=None,
            ngram_range=(1, 2)
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform([content])
            feature_names = vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            
            # 상위 키워드 선택
            keyword_scores = list(zip(feature_names, tfidf_scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            keywords = [kw for kw, score in keyword_scores[:10] if score > 0.1]
            return keywords
            
        except Exception as e:
            logger.warning(f"키워드 추출 실패: {str(e)}")
            return []
    
    def _extract_description_from_gri_section(self, content: str) -> str:
        """GRI 섹션에서 설명 추출"""
        # 첫 번째 문단을 설명으로 사용
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if len(para.strip()) > 50:
                return para.strip()[:500]  # 최대 500자
        
        return content[:500]
    
    async def create_enhanced_keyword_mapping(self) -> Dict:
        """향상된 키워드 매핑 생성"""
        enhanced_mapping = {}
        
        # 기존 하드코딩 매핑 확장
        base_keywords = {
            "환경": ["환경", "기후", "탄소", "온실가스", "재생에너지", "친환경", "지속가능", "녹색"],
            "사회": ["사회", "임직원", "인권", "다양성", "안전", "보건", "지역사회", "사회공헌"],
            "지배구조": ["지배구조", "이사회", "투명성", "윤리", "컴플라이언스", "리스크", "감사"]
        }
        
        # GRI 표준 기반 키워드 추가
        for gri_code, gri_data in self.gri_standards.items():
            category = self._categorize_gri_standard(gri_code)
            
            if category in base_keywords:
                # 기존 키워드에 GRI 키워드 추가
                base_keywords[category].extend(gri_data["keywords"])
                # 중복 제거
                base_keywords[category] = list(set(base_keywords[category]))
        
        # 키워드별 GRI 매핑 생성
        for category, keywords in base_keywords.items():
            for keyword in keywords:
                best_gri = self._find_best_gri_match(keyword)
                if best_gri:
                    enhanced_mapping[keyword] = best_gri
        
        return {
            "enhanced_keywords": base_keywords,
            "keyword_to_gri_mapping": enhanced_mapping,
            "gri_standards": self.gri_standards
        }
    
    def _categorize_gri_standard(self, gri_code: str) -> str:
        """GRI 표준을 ESG 카테고리로 분류"""
        environmental_codes = ["302", "303", "304", "305", "306", "307", "308"]
        social_codes = ["401", "402", "403", "404", "405", "406", "407", "408", "409", "410", "411", "412", "413", "414", "415", "416", "417", "418", "419"]
        governance_codes = ["201", "202", "203", "204", "205", "206", "207"]
        
        gri_number = re.search(r'GRI\s+(\d+)', gri_code)
        if gri_number:
            number = gri_number.group(1)
            if number in environmental_codes:
                return "환경"
            elif number in social_codes:
                return "사회"
            elif number in governance_codes:
                return "지배구조"
        
        return "기타"
    
    def _find_best_gri_match(self, keyword: str) -> Optional[str]:
        """키워드에 가장 적합한 GRI 표준 찾기"""
        if not self.gri_embeddings:
            return None
        
        keyword_embedding = self.sbert_model.encode(keyword)
        best_match = None
        best_score = 0.0
        
        for gri_code, gri_embedding in self.gri_embeddings.items():
            similarity = cosine_similarity(
                np.array([keyword_embedding]), 
                np.array([gri_embedding])
            )[0][0]
            if similarity > best_score and similarity > 0.3:  # 임계값 0.3
                best_score = similarity
                best_match = gri_code
        
        return best_match
    
    async def generate_training_data_from_gri(self, output_path: str) -> str:
        """GRI Standard 기반 훈련 데이터 생성"""
        training_data = []
        
        for gri_code, gri_data in self.gri_standards.items():
            # 분류 데이터 생성
            for keyword in gri_data["keywords"]:
                training_data.append({
                    "text": f"{keyword}에 대한 ESG 보고서 내용입니다: {gri_data['description'][:200]}",
                    "labels": 1,  # ESG 관련
                    "gri_standard": gri_code,
                    "category": self._categorize_gri_standard(gri_code)
                })
            
            # QA 데이터 생성
            training_data.append({
                "question": f"{gri_code}에 대해 설명해주세요.",
                "context": gri_data["description"],
                "answers": {
                    "text": [gri_data["description"][:100]],
                    "answer_start": [0]
                },
                "gri_standard": gri_code
            })
        
        # 데이터프레임으로 변환 및 저장
        df = pd.DataFrame(training_data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"✅ GRI 기반 훈련 데이터 생성 완료: {len(training_data)}개 샘플")
        return output_path
    
    async def save_enhanced_mapping(self, output_path: str) -> str:
        """향상된 키워드 매핑 저장"""
        enhanced_mapping = await self.create_enhanced_keyword_mapping()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_mapping, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 향상된 키워드 매핑 저장 완료: {output_path}")
        return output_path
    
    def _generate_simple_training_data(self, gri_number: str, gri_title: str, 
                                     category: str, file_name: str, text_sample: str) -> List[Dict]:
        """간단한 학습 데이터 생성 (PDF 파싱 문제 해결용)"""
        training_data = []
        
        # 1. GRI 표준 설명 학습
        training_data.append({
            "input_text": f"GRI {gri_number}에 대해 설명해주세요.",
            "target_text": f"GRI {gri_number} ({gri_title})는 {category} 카테고리의 표준입니다. 이 표준은 지속가능성 보고에서 중요한 역할을 합니다.",
            "gri_standard": gri_number,
            "gri_title": gri_title,
            "category": category,
            "task_type": "standard_explanation",
            "source_file": file_name
        })
        
        # 2. 카테고리 분류 학습
        training_data.append({
            "input_text": f"GRI {gri_number} {gri_title}는 어떤 ESG 카테고리에 속하나요?",
            "target_text": f"GRI {gri_number} {gri_title}는 {category} 카테고리에 속합니다.",
            "gri_standard": gri_number,
            "gri_title": gri_title,
            "category": category,
            "task_type": "category_classification",
            "source_file": file_name
        })
        
        # 3. 키워드 매칭 학습
        keywords = self._get_category_keywords(category)
        if keywords:
            keyword_text = ", ".join(keywords[:3])
            training_data.append({
                "input_text": f"'{keyword_text}' 키워드와 관련된 GRI 표준은 무엇인가요?",
                "target_text": f"'{keyword_text}' 키워드는 GRI {gri_number} ({gri_title}) 표준과 관련됩니다.",
                "gri_standard": gri_number,
                "gri_title": gri_title,
                "category": category,
                "task_type": "keyword_matching",
                "keywords": keyword_text,
                "source_file": file_name
            })
        
        return training_data
    
    def _get_category_keywords(self, category: str) -> List[str]:
        """카테고리별 대표 키워드 반환"""
        category_keywords = {
            "Environmental": ["emission", "energy", "water", "waste", "biodiversity"],
            "Social": ["employment", "training", "diversity", "health", "safety"],
            "Economic": ["economic performance", "market presence", "procurement"],
            "Foundation & General": ["materiality", "stakeholder", "disclosure"]
        }
        return category_keywords.get(category, [])

    def _find_gri_files(self):
        """GRI PDF 파일들을 찾는 메서드"""
        gri_files = []
        for root, _, files in os.walk(self.gri_folder):
            for file in files:
                if file.endswith(('.pdf', '.PDF')):
                    gri_files.append(os.path.join(root, file))
        return gri_files

    def _parse_gri_info_from_filename(self, file_path: str) -> Dict:
        """파일명에서 GRI 정보 추출"""
        gri_info = {
            "number": "Unknown",
            "title": "Unknown", 
            "year": "Unknown",
            "category": "Unknown"
        }
        
        try:
            if "GRI " in file_path:
                parts = file_path.split("GRI ")[1]
                
                if "_" in parts:
                    number_part = parts.split("_")[0].strip()
                    title_part = parts.split("_")[1].split(".pdf")[0].strip()
                    
                    # 연도 추출
                    year_match = re.search(r'\d{4}', title_part)
                    if year_match:
                        gri_info["year"] = year_match.group()
                        title_part = re.sub(r'\d{4}', '', title_part).strip()
                    
                    gri_info["number"] = number_part
                    gri_info["title"] = title_part
                    gri_info["category"] = self._categorize_gri_standard_by_number(number_part)
                    
        except Exception as e:
            logger.warning(f"파일명 파싱 실패: {file_path} - {str(e)}")
        
        return gri_info 