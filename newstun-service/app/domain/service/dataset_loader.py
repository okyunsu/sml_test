import json
import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class DatasetLoader:
    """JSON 샘플 데이터셋 로더"""
    
    def __init__(self):
        # 기본 경로 설정
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.sample_datasets_dir = os.path.join(self.base_dir, "app", "sample_datasets")
        self.training_data_dir = os.path.join(self.base_dir, "data", "training")
        
        # 디렉토리 생성
        os.makedirs(self.training_data_dir, exist_ok=True)
        
        logger.info(f"DatasetLoader 초기화:")
        logger.info(f"  - 기본 디렉토리: {self.base_dir}")
        logger.info(f"  - 샘플 데이터셋 디렉토리: {self.sample_datasets_dir}")
        logger.info(f"  - 훈련 데이터 디렉토리: {self.training_data_dir}")
    
    async def load_json_dataset(self, json_file_path: str) -> List[Dict[str, Any]]:
        """JSON 파일에서 데이터셋 로드"""
        try:
            if not os.path.exists(json_file_path):
                raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {json_file_path}")
            
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 데이터 형식 검증
            if isinstance(data, list):
                dataset = data
            elif isinstance(data, dict) and "data" in data:
                dataset = data["data"]
            elif isinstance(data, dict) and "news_data" in data:
                dataset = data["news_data"]
            else:
                raise ValueError("JSON 파일 형식이 올바르지 않습니다. 리스트 또는 {'data': []} 형식이어야 합니다.")
            
            logger.info(f"JSON 데이터셋 로드 완료: {len(dataset)}개 항목")
            return dataset
            
        except Exception as e:
            logger.error(f"JSON 데이터셋 로드 중 오류: {str(e)}")
            raise
    
    async def convert_json_to_training_format(self, json_file_path: str) -> Dict[str, Any]:
        """JSON 데이터셋을 훈련용 CSV 형식으로 변환"""
        try:
            logger.info(f"JSON 데이터셋 변환 시작: {json_file_path}")
            
            # JSON 파일 로드
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list) or len(data) == 0:
                raise ValueError("유효하지 않은 JSON 데이터 형식입니다")
            
            # 데이터프레임 생성
            df = pd.DataFrame(data)
            
            # 현재 JSON 구조에 맞게 필수 컬럼 확인 (text, category, sentiment)
            if 'text' in df.columns:
                # 현재 JSON 구조: text 필드 사용
                required_columns = ['text', 'category', 'sentiment']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
                
                # 카테고리 분류용 데이터셋 생성
                category_df = df[['text', 'category']].copy()
                category_df = category_df.rename(columns={'category': 'category_label'})
                
                # 감정 분석용 데이터셋 생성
                sentiment_df = df[['text', 'sentiment']].copy()
                sentiment_df = sentiment_df.rename(columns={'sentiment': 'sentiment_label'})
            elif 'title' in df.columns and 'content' in df.columns:
                # 기존 구조: title, content 필드 사용
                required_columns = ['title', 'content', 'category', 'sentiment']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
                    
                # 카테고리 분류용 데이터셋 생성
                category_df = df[['title', 'content', 'category']].copy()
                category_df['text'] = category_df['title'] + ' ' + category_df['content']
                category_df = category_df[['text', 'category']].rename(columns={'category': 'category_label'})
                
                # 감정 분석용 데이터셋 생성
                sentiment_df = df[['title', 'content', 'sentiment']].copy()
                sentiment_df['text'] = sentiment_df['title'] + ' ' + sentiment_df['content']
                sentiment_df = sentiment_df[['text', 'sentiment']].rename(columns={'sentiment': 'sentiment_label'})
            else:
                raise ValueError("text 필드 또는 title/content 필드가 필요합니다")
            
            # 파일명 기반 출력 파일명 생성
            base_name = os.path.splitext(os.path.basename(json_file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            category_file = os.path.join(self.training_data_dir, f"category_dataset_{base_name}_{timestamp}.csv")
            category_df.to_csv(category_file, index=False, encoding='utf-8')
            
            sentiment_file = os.path.join(self.training_data_dir, f"sentiment_dataset_{base_name}_{timestamp}.csv")
            sentiment_df.to_csv(sentiment_file, index=False, encoding='utf-8')
            
            # 통계 정보
            category_stats = df['category'].value_counts().to_dict()
            sentiment_stats = df['sentiment'].value_counts().to_dict()
            
            result = {
                "success": True,
                "input_file": json_file_path,
                "total_items": len(df),
                "files": {
                    "category_dataset": category_file,
                    "sentiment_dataset": sentiment_file
                },
                "file_sizes": {
                    "category_dataset_size": os.path.getsize(category_file),
                    "sentiment_dataset_size": os.path.getsize(sentiment_file)
                },
                "statistics": {
                    "categories": category_stats,
                    "sentiments": sentiment_stats
                }
            }
            
            logger.info(f"데이터셋 변환 완료:")
            logger.info(f"  - 카테고리 데이터셋: {category_file} ({os.path.getsize(category_file)} bytes)")
            logger.info(f"  - 감정 데이터셋: {sentiment_file} ({os.path.getsize(sentiment_file)} bytes)")
            
            return result
            
        except Exception as e:
            logger.error(f"데이터셋 변환 실패: {str(e)}")
            raise
    
    def _validate_and_clean_item(self, item: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """데이터 항목 검증 및 정제"""
        try:
            # 필수 필드 확인
            text = item.get("text", "").strip()
            
            if not text:
                logger.warning(f"항목 {index}: 텍스트가 비어있음")
                return None
            
            if len(text) < 10:
                logger.warning(f"항목 {index}: 텍스트가 너무 짧음 ({len(text)}자)")
                return None
            
            # 카테고리 정규화 - JSON 데이터셋의 실제 카테고리에 맞게 수정
            category = item.get("category", "기타").strip()
            category_mapping = {
                "E": "환경(E)",
                "S": "사회(S)", 
                "G": "지배구조(G)",
                "재무정보": "재무",
                "ESG": "ESG",
                "재무": "재무"
            }
            
            mapped_category = category_mapping.get(category, "기타")
            if mapped_category == "기타":
                logger.warning(f"항목 {index}: 알 수 없는 카테고리 '{category}' -> '기타'로 변경")
            
            # 감정 정규화
            sentiment = item.get("sentiment", "중립").strip()
            if sentiment not in ["긍정", "부정", "중립"]:
                logger.warning(f"항목 {index}: 알 수 없는 감정 '{sentiment}' -> '중립'로 변경")
                sentiment = "중립"
            
            return {
                "text": text,
                "category_label": mapped_category,
                "sentiment_label": sentiment,
                "original_category": category,
                "url": item.get("url", ""),
                "date": item.get("date", ""),
                "id": item.get("id", f"item_{index}"),
                "original_index": index
            }
            
        except Exception as e:
            logger.error(f"항목 {index} 검증 중 오류: {str(e)}")
            return None
    
    async def list_sample_datasets(self) -> List[Dict[str, Any]]:
        """sample_datasets 폴더의 JSON 파일 목록 조회"""
        try:
            datasets = []
            
            if not os.path.exists(self.sample_datasets_dir):
                logger.warning(f"샘플 데이터셋 디렉토리가 존재하지 않습니다: {self.sample_datasets_dir}")
                return datasets
            
            for filename in os.listdir(self.sample_datasets_dir):
                if filename.endswith('.json') and not filename.startswith('__'):
                    file_path = os.path.join(self.sample_datasets_dir, filename)
                    try:
                        file_stat = os.stat(file_path)
                        datasets.append({
                            "filename": filename,
                            "path": file_path,
                            "size_bytes": file_stat.st_size,
                            "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                            "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                        })
                    except Exception as e:
                        logger.error(f"파일 정보 조회 실패 {filename}: {str(e)}")
                        continue
            
            logger.info(f"샘플 데이터셋 {len(datasets)}개 발견")
            return datasets
            
        except Exception as e:
            logger.error(f"샘플 데이터셋 목록 조회 실패: {str(e)}")
            raise
    
    async def validate_json_format(self, json_file_path: str) -> Dict[str, Any]:
        """JSON 데이터셋 형식 검증"""
        try:
            logger.info(f"JSON 형식 검증 시작: {json_file_path}")
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON 데이터는 리스트 형태여야 합니다")
            
            if len(data) == 0:
                raise ValueError("JSON 데이터가 비어있습니다")
            
            # 필수 필드 검증 - 현재 JSON 구조에 맞게 수정
            sample_item = data[0]
            
            # text 필드 기반 또는 title/content 필드 기반 검증
            if 'text' in sample_item:
                required_fields = ['text', 'category', 'sentiment']
            elif 'title' in sample_item and 'content' in sample_item:
                required_fields = ['title', 'content', 'category', 'sentiment']
            else:
                raise ValueError("text 필드 또는 title/content 필드가 필요합니다")
            
            missing_fields = [field for field in required_fields if field not in sample_item]
            if missing_fields:
                raise ValueError(f"필수 필드가 누락되었습니다: {missing_fields}")
            
            # 데이터 통계
            categories = {}
            sentiments = {}
            
            for item in data:
                # 카테고리 통계
                category = item.get('category', 'Unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # 감정 통계
                sentiment = item.get('sentiment', 'Unknown')
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            validation_result = {
                "valid": True,
                "total_items": len(data),
                "required_fields": required_fields,
                "sample_item": sample_item,
                "statistics": {
                    "categories": categories,
                    "sentiments": sentiments
                }
            }
            
            logger.info(f"JSON 형식 검증 완료: {len(data)}개 항목")
            return validation_result
            
        except Exception as e:
            logger.error(f"JSON 형식 검증 실패: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "total_items": 0
            } 