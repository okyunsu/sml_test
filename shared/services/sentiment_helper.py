"""
감정 분석 변환 헬퍼
SASB 서비스 등에서 사용하는 공통 감정 라벨 변환 기능
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SentimentConverter:
    """감정 분석 라벨 변환 도우미 클래스"""
    
    # 감정 라벨 매핑 (label_encoder.json 기준)
    LABEL_MAPPING = {
        "LABEL_0": "긍정",
        "0": "긍정", 
        "LABEL_1": "부정",
        "1": "부정",
        "LABEL_2": "중립", 
        "2": "중립",
        # 이미 변환된 형태
        "긍정": "긍정",
        "부정": "부정", 
        "중립": "중립",
        # 영문 형태
        "POSITIVE": "긍정",
        "POS": "긍정",
        "NEGATIVE": "부정", 
        "NEG": "부정",
        "NEUTRAL": "중립",
        "NEU": "중립"
    }
    
    SENTIMENT_SCORES = {
        "긍정": 1,
        "부정": -1,
        "중립": 0
    }
    
    @classmethod
    def convert_sentiment_label(cls, raw_sentiment: Optional[str]) -> str:
        """
        원시 감정 라벨을 사람이 읽기 쉬운 형태로 변환
        
        LABEL_0, LABEL_1, LABEL_2를 긍정/부정/중립으로 변환
        기존 캐시된 데이터와 새로운 분석 결과 모두에 적용
        
        일반적인 3-class sentiment 분류:
        - LABEL_0 / 0 = 긍정 (positive)
        - LABEL_1 / 1 = 부정 (negative) 
        - LABEL_2 / 2 = 중립 (neutral)
        
        Args:
            raw_sentiment: 원시 감정 라벨
            
        Returns:
            변환된 감정 라벨 ("긍정", "부정", "중립")
        """
        if not raw_sentiment:
            return "중립"
            
        label = str(raw_sentiment).upper().strip()
        
        # 매핑에서 찾기
        converted = cls.LABEL_MAPPING.get(label)
        
        if converted:
            return converted
        else:
            # 알 수 없는 라벨의 경우 중립으로 처리
            logger.warning(f"알 수 없는 sentiment 라벨: '{raw_sentiment}' → 중립으로 처리")
            return "중립"
    
    @classmethod 
    def get_sentiment_score(cls, sentiment_label: str) -> int:
        """
        감정 라벨을 수치 점수로 변환
        
        Args:
            sentiment_label: 감정 라벨
            
        Returns:
            감정 점수 (긍정: 1, 중립: 0, 부정: -1)
        """
        return cls.SENTIMENT_SCORES.get(sentiment_label, 0)
    
    @classmethod
    def convert_articles_sentiment(cls, articles: list) -> list:
        """
        뉴스 기사 리스트의 감정 라벨을 일괄 변환
        
        Args:
            articles: 뉴스 기사 리스트 (sentiment 키 포함)
            
        Returns:
            변환된 뉴스 기사 리스트
        """
        if not articles:
            return articles
            
        converted_articles = []
        for article in articles:
            if isinstance(article, dict) and 'sentiment' in article:
                article_copy = article.copy()
                article_copy['sentiment'] = cls.convert_sentiment_label(article['sentiment'])
                # 감정 점수도 추가
                article_copy['sentiment_score'] = cls.get_sentiment_score(article_copy['sentiment'])
                converted_articles.append(article_copy)
            else:
                converted_articles.append(article)
                
        return converted_articles 