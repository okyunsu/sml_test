from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import re
from collections import defaultdict
import math

from ..model.materiality_dto import MaterialityTopic, MaterialityAssessment
from .materiality_mapping_service import MaterialityMappingService

logger = logging.getLogger(__name__)

class NewsAnalysisEngine:
    """뉴스 데이터 분석 엔진
    
    sasb-service에서 수집한 뉴스 데이터를 분석하여:
    - 중대성 평가 토픽과의 관련성 점수 계산
    - sentiment 분석 결과 활용
    - 키워드 매칭 및 가중치 계산
    - 뉴스 빈도 및 중요도 분석
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mapping_service = MaterialityMappingService()
        
        # 🎯 중대성 토픽별 키워드 사전 (확장된 매핑)
        self.topic_keyword_dict = {
            "기후변화 대응": [
                # 핵심 키워드
                "기후변화", "탄소중립", "넷제로", "net zero", "탄소배출", "온실가스",
                "기후위기", "탄소감축", "에너지전환", "RE100", "K-RE100",
                
                # 두산퓨얼셀 특화 기술
                "연료전지", "수소연료전지", "SOFC", "고체산화물연료전지", "수소발전",
                "그린수소", "청정수소", "수소경제", "수소충전소", "수소모빌리티",
                
                # LS ELECTRIC 특화 기술
                "ESS", "에너지저장장치", "배터리저장시스템", "그리드연계",
                "스마트그리드", "마이크로그리드", "전력변환", "인버터", "PCS",
                
                # 공통 재생에너지 기술
                "재생에너지", "신재생에너지", "태양광", "풍력", "전기차", "EV", "배터리",
                
                # 정책/제도
                "탄소세", "배출권", "K-ETS", "ETS", "탄소국경세", "CBAM",
                "ESG", "지속가능", "파리협정", "TCFD", "SBTi"
            ],
            
            "공급망 관리 및 상생경영": [
                # 공급망 관리
                "공급망", "협력사", "파트너사", "벤더", "조달", "구매",
                "상생경영", "동반성장", "스마트팩토리", "디지털전환",
                
                # 위험 관리
                "공급망리스크", "supply chain", "ESG경영", "지속가능경영",
                "투명성", "추적가능성", "인권경영", "아동노동", "강제노동",
                
                # 관련 표준
                "ISO", "OECD", "UN Global Compact", "SA8000"
            ],
            
            "제품 에너지 효율 향상 및 환경영향 감소": [
                # 두산퓨얼셀 제품 효율성
                "연료전지효율", "수소이용효율", "발전효율", "열효율", "전력변환효율",
                "SOFC효율", "연료전지수명", "내구성", "성능개선", "출력밀도",
                
                # LS ELECTRIC 제품 효율성
                "전력효율", "변압기효율", "인버터효율", "모터효율", "전력손실",
                "고효율변압기", "IGBT", "SiC", "파워반도체", "전력변환",
                "무효전력", "역률개선", "고조파", "전력품질",
                
                # 공통 에너지 효율
                "에너지효율", "에너지절약", "고효율", "효율성", "절전",
                "스마트기기", "IoT", "AI", "빅데이터", "디지털트윈",
                
                # 환경 영향
                "환경영향", "환경친화", "친환경", "에코", "그린",
                "생애주기", "LCA", "Life Cycle Assessment", "탄소발자국",
                "자원순환", "폐기물감축", "재활용", "업사이클링",
                
                # 제품 혁신
                "제품혁신", "R&D", "연구개발", "기술개발", "특허",
                "차세대", "스마트", "디지털화", "자동화"
            ],
            
            "디지털 전환 및 사이버보안": [
                # 디지털 전환
                "디지털전환", "DX", "디지털화", "자동화", "스마트팩토리",
                "IoT", "AI", "인공지능", "빅데이터", "클라우드",
                "로봇", "RPA", "블록체인", "AR", "VR",
                
                # 사이버보안
                "사이버보안", "정보보안", "데이터보호", "개인정보", "해킹",
                "랜섬웨어", "보안솔루션", "암호화", "인증", "방화벽"
            ],
            
            "인재 육성 및 노동 안전": [
                # 인재 육성
                "인재육성", "교육훈련", "역량개발", "스킬업", "리스킬링",
                "업스킬링", "인재개발", "전문인력", "기술인력", "청년채용",
                
                # 노동 안전
                "안전", "산업안전", "작업안전", "안전사고", "재해",
                "안전보건", "KOSHA", "ISO45001", "안전관리",
                "보호구", "안전교육", "위험성평가"
            ],
            
            "거버넌스 및 윤리경영": [
                # 거버넌스
                "거버넌스", "이사회", "독립이사", "감사위원회",
                "내부통제", "컴플라이언스", "준법", "리스크관리",
                
                # 윤리경영
                "윤리경영", "투명경영", "반부패", "부패방지",
                "공정거래", "이해충돌", "내부신고", "윤리강령"
            ]
        }
        
        # 🎯 회사별 특화 키워드 (MVP 대상 기업)
        self.company_keywords = {
            "두산퓨얼셀": [
                # 핵심 비즈니스
                "연료전지", "SOFC", "고체산화물연료전지", "수소", "수소경제",
                "그린수소", "청정수소", "수소발전", "수소충전소", "수소모빌리티",
                "발전용연료전지", "가정용연료전지", "건물용연료전지",
                
                # 기술/제품
                "스택", "셀", "전해질", "전극", "개질기", "BOP",
                "발전효율", "내구성", "수명", "출력밀도", "시스템통합",
                
                # 산업 분야
                "에너지", "발전", "전력", "열병합", "분산전원", "마이크로그리드"
            ],
            "LS ELECTRIC": [
                # 핵심 비즈니스 
                "전력기기", "변압기", "차단기", "개폐기", "배전반", "수배전",
                "전력변환", "인버터", "컨버터", "PCS", "ESS", "에너지저장",
                "스마트그리드", "그리드연계", "전력계통", "송배전",
                
                # 기술/제품
                "IGBT", "SiC", "파워반도체", "전력용반도체", "모듈",
                "변압기효율", "손실", "절연", "냉각", "보호계전",
                "SCADA", "EMS", "자동화", "제어시스템",
                
                # 산업 분야
                "전력", "철도", "산업자동화", "빌딩자동화", "공장자동화",
                "신재생에너지", "태양광", "풍력", "배터리", "전기차"
            ],
            "한국중부발전": [
                # 핵심 비즈니스
                "화력발전", "발전소", "전력생산", "전력공급", "발전설비",
                "석탄화력", "LNG발전", "복합화력", "집단에너지", "열병합",
                "신재생에너지", "태양광", "풍력", "연료전지", "에너지저장",
                
                # 환경/기후변화
                "온실가스", "탄소중립", "탄소배출", "환경설비", "탈석탄",
                "에너지전환", "그린뉴딜", "친환경발전", "배출저감", "대기오염",
                "미세먼지", "질소산화물", "황산화물", "폐수처리", "폐기물",
                
                # 기술/시설
                "발전효율", "열효율", "설비개선", "정비", "보수", "점검",
                "터빈", "보일러", "발전기", "변압기", "송전", "배전",
                "스마트그리드", "ESS", "에너지저장장치", "계통연계",
                
                # 안전/운영
                "안전관리", "작업안전", "설비안전", "예방정비", "정전",
                "전력수급", "전력계통", "전력거래", "SMP", "용량요금",
                
                # 사회/지역
                "지역상생", "주민수용성", "환경영향평가", "발전단지",
                "일자리창출", "지역경제", "사회공헌", "상생협력"
            ]
        }
        
        # 가중치 설정 (조정됨)
        self.weights = {
            'title_match': 5.0,      # 제목 매칭 가중치 증가
            'content_match': 2.0,    # 본문 매칭 가중치 증가
            'exact_match': 3.0,      # 정확한 매칭 추가
            'partial_match': 1.0,    # 부분 매칭
            'sentiment_positive': 1.3,  # 긍정 sentiment 가중치
            'sentiment_negative': 0.9,  # 부정 sentiment 가중치
            'recent_news': 1.5,      # 최근 뉴스 가중치
            'keyword_density': 2.5,  # 키워드 밀도 가중치 증가
            'company_mention': 2.0   # 회사명 언급 가중치 추가
        }
        
        # 관련성 임계값 상향 조정
        self.relevance_threshold = 0.3  # 0.1 → 0.3으로 상향
    
    def analyze_news_for_materiality(
        self,
        news_articles: List[Dict[str, Any]],
        materiality_topics: List[MaterialityTopic],
        company_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """뉴스 기사들을 분석하여 중대성 평가 토픽별 관련성 점수 계산
        
        Args:
            news_articles: sasb-service에서 수집한 뉴스 기사 리스트
            materiality_topics: 중대성 평가 토픽 리스트
            company_name: 기업명
            
        Returns:
            Dict[str, Dict[str, Any]]: 토픽별 분석 결과
        """
        self.logger.info(f"📊 뉴스 분석 시작: {len(news_articles)}개 기사, {len(materiality_topics)}개 토픽")
        
        analysis_results = {}
        
        for topic in materiality_topics:
            topic_name = topic.topic_name
            
            # 1. 🎯 강화된 키워드 추출 (토픽 + 회사 특화)
            related_keywords = self.extract_enhanced_keywords(topic, company_name)
            
            # 2. 관련 뉴스 필터링 및 점수 계산
            topic_news_analysis = self._analyze_topic_news(
                news_articles, topic_name, related_keywords, company_name
            )
            
            # 3. 종합 점수 계산
            comprehensive_score = self._calculate_comprehensive_score(
                topic_news_analysis['articles'], related_keywords
            )
            
            # 4. 트렌드 분석
            trend_analysis = self._analyze_news_trend(topic_news_analysis['articles'])
            
            analysis_results[topic_name] = {
                'topic_name': topic_name,
                'related_keywords': related_keywords,
                'total_news_count': len(topic_news_analysis['articles']),
                'relevant_news_count': topic_news_analysis['relevant_count'],
                'comprehensive_score': comprehensive_score,
                'trend_analysis': trend_analysis,
                'top_articles': topic_news_analysis['top_articles'][:5],  # 상위 5개 기사
                'sentiment_distribution': topic_news_analysis['sentiment_distribution'],
                # 🎯 디버깅 정보 추가
                'debug_info': {
                    'keyword_count': len(related_keywords),
                    'sample_keywords': related_keywords[:10],  # 샘플 키워드
                    'relevance_threshold': self.relevance_threshold,
                    'top_matched_articles': [
                        {
                            'title': art['article'].get('title', '')[:100],
                            'relevance_score': art['relevance_score'],
                            'matched_keywords': art['matched_keywords'][:5]
                        }
                        for art in topic_news_analysis['top_articles'][:3]
                    ]
                }
            }
            
            self.logger.info(f"✅ {topic_name} 분석 완료: {topic_news_analysis['relevant_count']}/{len(news_articles)}개 관련 기사 (점수: {comprehensive_score:.3f})")
        
        self.logger.info(f"📈 전체 뉴스 분석 완료: {len(analysis_results)}개 토픽")
        return analysis_results
    
    def extract_enhanced_keywords(
        self, 
        topic: MaterialityTopic, 
        company_name: Optional[str] = None
    ) -> List[str]:
        """🎯 강화된 키워드 추출 - 토픽 + 회사 특화 키워드 조합"""
        keywords = []
        topic_name = topic.topic_name
        
        # 1. 🎯 토픽별 키워드 사전에서 매칭
        if topic_name in self.topic_keyword_dict:
            topic_keywords = self.topic_keyword_dict[topic_name]
            keywords.extend(topic_keywords)
            self.logger.info(f"📋 {topic_name}: {len(topic_keywords)}개 토픽 키워드 추가")
        
        # 2. 🎯 회사별 특화 키워드 추가 (MVP 대상 기업)
        if company_name and company_name in self.company_keywords:
            company_keywords = self.company_keywords[company_name]
            keywords.extend(company_keywords)
            self.logger.info(f"🏢 {company_name}: {len(company_keywords)}개 회사 키워드 추가")
        
        # 3. 토픽명 기반 유사성 매칭
        for dict_topic, dict_keywords in self.topic_keyword_dict.items():
            if topic_name != dict_topic:
                similarity = self._calculate_topic_similarity(topic_name, dict_topic)
                if similarity > 0.5:
                    keywords.extend(dict_keywords[:8])  # 상위 8개만
                    self.logger.info(f"🔗 유사 토픽 {dict_topic}: {similarity:.2f} 유사성, {len(dict_keywords[:8])}개 키워드 추가")
        
        # 4. 기본 키워드 추출 (보완)
        basic_keywords = self._extract_keywords_from_text(topic_name)
        keywords.extend(basic_keywords)
        
        # 5. SASB 매핑 키워드 (보완)
        try:
            sasb_keywords = self.mapping_service.find_related_keywords(topic_name)
            keywords.extend(sasb_keywords.get('industry_keywords', [])[:5])
            keywords.extend(sasb_keywords.get('sasb_keywords', [])[:5])
        except Exception as e:
            self.logger.warning(f"SASB 키워드 추출 실패: {e}")
        
        # 6. 중복 제거 및 정제
        unique_keywords = list(set(keywords))
        cleaned_keywords = [kw.strip() for kw in unique_keywords if len(kw.strip()) > 1]
        
        self.logger.info(f"✅ {topic_name} ({company_name or 'N/A'}): 총 {len(cleaned_keywords)}개 키워드 추출")
        return cleaned_keywords
    
    def _extract_topic_keywords(self, topic: MaterialityTopic) -> List[str]:
        """토픽 키워드 추출 (하위 호환성 유지)"""
        return self.extract_enhanced_keywords(topic, None)
    
    def _calculate_topic_similarity(self, topic1: str, topic2: str) -> float:
        """토픽명 간 유사성 계산"""
        # 간단한 키워드 겹침 기반 유사성 계산
        words1 = set(topic1.split())
        words2 = set(topic2.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 기본적인 키워드 추출 로직
        keywords = []
        
        # 1. 공백으로 분리
        words = text.split()
        keywords.extend([word.strip() for word in words if len(word.strip()) > 1])
        
        # 2. 특수 문자 제거 및 정제
        cleaned_keywords = []
        for keyword in keywords:
            # 특수 문자 제거 (한글, 영문, 숫자만 유지)
            cleaned = re.sub(r'[^\w\s가-힣]', '', keyword)
            if len(cleaned) > 1:
                cleaned_keywords.append(cleaned)
        
        return cleaned_keywords
    
    def _analyze_topic_news(
        self,
        news_articles: List[Dict[str, Any]],
        topic_name: str,
        related_keywords: List[str],
        company_name: str
    ) -> Dict[str, Any]:
        """토픽별 뉴스 분석"""
        relevant_articles = []
        sentiment_distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for article in news_articles:
            # 1. 관련성 점수 계산
            relevance_score = self._calculate_article_relevance(
                article, related_keywords, company_name
            )
            
            # 2. 관련성 임계값 적용
            if relevance_score > self.relevance_threshold:  # 최소 관련성 임계값
                article_analysis = {
                    'article': article,
                    'relevance_score': relevance_score,
                    'matched_keywords': self._find_matched_keywords(article, related_keywords)
                }
                relevant_articles.append(article_analysis)
                
                # 3. sentiment 분포 업데이트
                sentiment = article.get('sentiment', 'neutral')
                if sentiment in sentiment_distribution:
                    sentiment_distribution[sentiment] += 1
        
        # 4. 관련성 점수 기준으로 정렬
        relevant_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return {
            'articles': relevant_articles,
            'relevant_count': len(relevant_articles),
            'top_articles': relevant_articles[:10],  # 상위 10개
            'sentiment_distribution': sentiment_distribution
        }
    
    def _calculate_article_relevance(
        self,
        article: Dict[str, Any],
        keywords: List[str],
        company_name: str
    ) -> float:
        """🎯 개선된 기사 관련성 점수 계산"""
        title = article.get('title', '')
        content = article.get('content', '') or article.get('summary', '') or article.get('description', '')
        sentiment = article.get('sentiment', 'neutral')
        published_at = article.get('published_at', '')
        
        total_score = 0.0
        
        # 1. 🎯 제목에서 정확한 키워드 매칭 (가중치 높음)
        title_exact_matches = self._count_exact_keyword_matches(title, keywords)
        title_partial_matches = self._count_partial_keyword_matches(title, keywords)
        total_score += title_exact_matches * self.weights['title_match'] * self.weights['exact_match']
        total_score += title_partial_matches * self.weights['title_match'] * self.weights['partial_match']
        
        # 2. 🎯 본문에서 정확한 키워드 매칭
        content_exact_matches = self._count_exact_keyword_matches(content, keywords)
        content_partial_matches = self._count_partial_keyword_matches(content, keywords)
        total_score += content_exact_matches * self.weights['content_match'] * self.weights['exact_match']
        total_score += content_partial_matches * self.weights['content_match'] * self.weights['partial_match']
        
        # 3. 기업명 매칭 보너스
        if company_name.lower() in title.lower() or company_name.lower() in content.lower():
            total_score += self.weights['company_mention']
        
        # 4. sentiment 가중치 적용
        if sentiment == 'positive':
            total_score *= self.weights['sentiment_positive']
        elif sentiment == 'negative':
            total_score *= self.weights['sentiment_negative']
        
        # 5. 최근성 가중치 적용
        if self._is_recent_news(published_at):
            total_score *= self.weights['recent_news']
        
        # 6. 키워드 밀도 가중치
        keyword_density = self._calculate_keyword_density(title + ' ' + content, keywords)
        total_score += keyword_density * self.weights['keyword_density']
        
        return total_score
    
    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """텍스트에서 키워드 매칭 개수 계산"""
        if not text:
            return 0
        
        text_lower = text.lower()
        matches = 0
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches += 1
        
        return matches
    
    def _count_exact_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """🎯 정확한 키워드 매칭 개수 계산 (단어 경계 고려)"""
        if not text:
            return 0
        
        text_lower = text.lower()
        matches = 0
        
        import re
        for keyword in keywords:
            # 단어 경계를 고려한 정확한 매칭
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matches += 1
        
        return matches
    
    def _count_partial_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """🎯 부분 키워드 매칭 개수 계산 (포함 관계)"""
        if not text:
            return 0
        
        text_lower = text.lower()
        exact_matches = self._count_exact_keyword_matches(text, keywords)
        total_matches = self._count_keyword_matches(text, keywords)
        
        # 부분 매칭 = 전체 매칭 - 정확한 매칭
        return max(0, total_matches - exact_matches)
    
    def _find_matched_keywords(self, article: Dict[str, Any], keywords: List[str]) -> List[str]:
        """기사에서 매칭된 키워드 찾기"""
        title = article.get('title', '')
        content = article.get('content', '') or article.get('summary', '')
        full_text = (title + ' ' + content).lower()
        
        matched = []
        for keyword in keywords:
            if keyword.lower() in full_text:
                matched.append(keyword)
        
        return matched
    
    def _is_recent_news(self, published_at: str) -> bool:
        """최근 뉴스인지 확인 (30일 이내)"""
        try:
            if not published_at:
                return False
            
            # 다양한 날짜 형식 처리
            import dateutil.parser
            pub_date = dateutil.parser.parse(published_at)
            now = datetime.now()
            days_diff = (now - pub_date).days
            
            return days_diff <= 30
        except:
            return False
    
    def _calculate_keyword_density(self, text: str, keywords: List[str]) -> float:
        """키워드 밀도 계산"""
        if not text or not keywords:
            return 0.0
        
        text_lower = text.lower()
        total_words = len(text_lower.split())
        
        if total_words == 0:
            return 0.0
        
        keyword_count = 0
        for keyword in keywords:
            keyword_count += text_lower.count(keyword.lower())
        
        return keyword_count / total_words
    
    def _calculate_comprehensive_score(
        self,
        articles: List[Dict[str, Any]],
        keywords: List[str]
    ) -> float:
        """종합 점수 계산"""
        if not articles:
            return 0.0
        
        # 1. 평균 관련성 점수
        avg_relevance = sum(article['relevance_score'] for article in articles) / len(articles)
        
        # 2. 뉴스 개수 가중치 (로그 스케일)
        news_count_weight = math.log(len(articles) + 1)
        
        # 3. 키워드 커버리지 (매칭된 키워드 비율)
        if keywords:
            all_matched_keywords = set()
            for article in articles:
                all_matched_keywords.update(article.get('matched_keywords', []))
            keyword_coverage = len(all_matched_keywords) / len(keywords)
        else:
            keyword_coverage = 0.0
        
        # 4. 종합 점수 계산
        comprehensive_score = (
            avg_relevance * 0.4 +
            news_count_weight * 0.3 +
            keyword_coverage * 0.3
        )
        
        return round(comprehensive_score, 3)
    
    def _analyze_news_trend(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """뉴스 트렌드 분석"""
        if not articles:
            return {
                'trend_direction': 'stable',
                'recent_increase': False,
                'peak_period': None,
                'avg_sentiment': 'neutral'
            }
        
        # 1. 날짜별 뉴스 분포
        date_distribution = defaultdict(int)
        sentiment_scores = []
        
        for article in articles:
            article_data = article.get('article', {})
            published_at = article_data.get('published_at', '')
            sentiment = article_data.get('sentiment', 'neutral')
            
            try:
                import dateutil.parser
                pub_date = dateutil.parser.parse(published_at)
                date_key = pub_date.strftime('%Y-%m')
                date_distribution[date_key] += 1
                
                # sentiment 점수화
                if sentiment == 'positive':
                    sentiment_scores.append(1)
                elif sentiment == 'negative':
                    sentiment_scores.append(-1)
                else:
                    sentiment_scores.append(0)
            except:
                continue
        
        # 2. 트렌드 방향 분석
        if len(date_distribution) >= 2:
            dates = sorted(date_distribution.keys())
            recent_count = date_distribution[dates[-1]]
            prev_count = date_distribution[dates[-2]] if len(dates) >= 2 else 0
            
            if recent_count > prev_count * 1.5:
                trend_direction = 'increasing'
                recent_increase = True
            elif recent_count < prev_count * 0.5:
                trend_direction = 'decreasing'
                recent_increase = False
            else:
                trend_direction = 'stable'
                recent_increase = False
        else:
            trend_direction = 'stable'
            recent_increase = False
        
        # 3. 평균 sentiment
        if sentiment_scores:
            avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
            if avg_sentiment_score > 0.2:
                avg_sentiment = 'positive'
            elif avg_sentiment_score < -0.2:
                avg_sentiment = 'negative'
            else:
                avg_sentiment = 'neutral'
        else:
            avg_sentiment = 'neutral'
        
        # 4. 피크 기간 찾기
        peak_period = max(date_distribution.keys(), key=lambda x: date_distribution[x]) if date_distribution else None
        
        return {
            'trend_direction': trend_direction,
            'recent_increase': recent_increase,
            'peak_period': peak_period,
            'avg_sentiment': avg_sentiment,
            'monthly_distribution': dict(date_distribution)
        } 