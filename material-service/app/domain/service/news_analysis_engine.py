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
        
        # 🎯 중대성 토픽별 키워드 사전 (광범위한 매핑)
        self.topic_keyword_dict = {
            "기후변화 대응": [
                # 🌱 기본 환경/기후 키워드 (뉴스에서 자주 사용)
                "기후변화", "기후위기", "지구온난화", "온실가스", "탄소배출", "탄소중립", 
                "넷제로", "탄소감축", "탄소저감", "친환경", "그린", "청정", "에코",
                "지속가능", "ESG", "환경", "환경보호", "환경규제", "환경정책",
                
                # ⚡ 에너지 전환 (일반적 표현)
                "에너지전환", "재생에너지", "신재생에너지", "신에너지", "청정에너지",
                "RE100", "에너지정책", "에너지믹스", "전원믹스", "에너지효율",
                
                # 🔋 구체적 기술 (간단한 용어)
                "연료전지", "수소", "수소연료전지", "수소발전", "수소경제", "그린수소",
                "태양광", "풍력", "ESS", "배터리", "에너지저장", "전기차", "EV",
                "스마트그리드", "마이크로그리드", "전력변환", "인버터",
                
                # 📋 정책/제도 (간단한 표현)
                "탄소세", "배출권", "탄소국경세", "K-ETS", "파리협정", "TCFD",
                "그린뉴딜", "한국판뉴딜", "탄소감축목표", "2050탄소중립"
            ],
            
            "순환경제": [
                # ♻️ 기본 순환경제 키워드
                "순환경제", "자원순환", "재활용", "재사용", "재제조", "업사이클링",
                "폐기물", "폐기물감축", "폐기물처리", "폐기물관리", "제로웨이스트",
                "자원효율", "자원절약", "자원관리", "원료회수", "소재회수",
                
                # 🔄 구체적 재활용 분야
                "폐배터리", "배터리재활용", "폐패널", "태양광패널재활용", "폐플라스틱",
                "금속재활용", "희토류", "핵심광물", "핵심소재", "원료확보",
                
                # 🏭 산업 연계
                "생산공정", "제조공정", "공정개선", "효율성", "생산성",
                "원가절감", "비용절감", "원료비", "소재비"
            ],
            
            "제품 환경영향 저감": [
                # 🌍 환경영향 기본 키워드
                "환경영향", "환경친화", "친환경제품", "그린제품", "에코제품",
                "환경성능", "환경효과", "환경개선", "오염저감", "배출저감",
                "대기오염", "수질오염", "토양오염", "소음", "진동",
                
                # ⚡ 제품 효율성 (일반적 표현)
                "효율성", "고효율", "에너지효율", "전력효율", "발전효율",
                "성능", "성능개선", "성능향상", "품질", "품질개선",
                "기술개발", "R&D", "연구개발", "혁신", "기술혁신",
                
                # 🔧 구체적 기술 (간단한 용어)
                "연료전지", "수소기술", "발전기술", "전력기술", "변압기",
                "인버터", "전력변환", "배터리기술", "저장기술",
                "스마트기술", "디지털기술", "자동화", "IoT", "AI",
                
                # 📊 성과/평가
                "LCA", "생애주기", "탄소발자국", "환경라벨", "인증",
                "환경인증", "품질인증", "성능인증", "효율등급"
            ],
            
            "사업장 안전보건": [
                # 🚨 기본 안전 키워드 (뉴스에서 자주 사용)
                "안전", "안전사고", "산업안전", "작업안전", "사고", "재해",
                "산업재해", "중대재해", "안전관리", "안전보건", "위험",
                "위험요소", "안전점검", "안전교육", "안전훈련",
                
                # ⚠️ 구체적 사고 유형
                "화재", "폭발", "감전", "추락", "낙하", "협착", "끼임",
                "가스누출", "화학물질", "유독가스", "질식", "화상",
                
                # 🏭 산업별 안전 (발전/전기 분야)
                "발전소안전", "전기안전", "고압전기", "정전", "전력사고",
                "설비안전", "장비안전", "보일러", "터빈", "변압기사고",
                
                # 📋 안전 제도/관리
                "안전수칙", "안전규정", "중대재해처벌법", "KOSHA", "안전보건공단",
                "안전관리자", "보건관리자", "위험성평가", "안전진단",
                "예방", "예방조치", "안전대책", "개선조치"
            ],
            
            "반부패 윤리경영 강화": [
                # 🏛️ 기본 윤리/거버넌스 키워드
                "윤리", "윤리경영", "투명", "투명성", "투명경영", "거버넌스",
                "기업지배구조", "컴플라이언스", "준법", "법규준수",
                "내부통제", "리스크관리", "위험관리",
                
                # 🚫 반부패 관련
                "부패", "반부패", "부패방지", "비리", "비위", "횡령",
                "배임", "뇌물", "후방공급", "특혜", "이해충돌",
                "공정거래", "담합", "카르텔", "독과점",
                
                # 🔍 조사/감사
                "감사", "내부감사", "외부감사", "검찰수사", "검찰조사",
                "국정감사", "국감", "조사", "수사", "기소", "처벌",
                "제재", "과징금", "벌금", "영업정지",
                
                # 📋 관련 제도
                "이사회", "독립이사", "감사위원회", "내부신고", "신고제도",
                "윤리강령", "행동강령", "준법통제", "준법감시"
            ],
            
            "고용 및 노사관계": [
                # 👥 기본 고용 키워드
                "고용", "채용", "인력", "인재", "직원", "근로자", "임직원",
                "일자리", "취업", "구인", "구직", "청년고용", "신입사원",
                "경력직", "인력충원", "인력확대", "인력감축",
                
                # 🤝 노사관계
                "노사", "노사관계", "노동조합", "노조", "파업", "태업",
                "단체교섭", "임금교섭", "협상", "합의", "갈등", "대립",
                "노사협력", "노사화합", "상생", "상생협력",
                
                # 💰 임금/복리후생
                "임금", "급여", "연봉", "보너스", "성과급", "인센티브",
                "복리후생", "복지", "수당", "휴가", "육아휴직",
                "워라밸", "일생활균형", "근무환경", "근무조건",
                
                # 📚 교육/개발
                "교육", "훈련", "교육훈련", "역량개발", "인재개발",
                "스킬업", "리스킬링", "업스킬링", "전문교육",
                "승진", "인사", "인사제도", "평가", "성과평가"
            ],
            
            "지속가능한 공급망 관리": [
                # 🔗 기본 공급망 키워드
                "공급망", "협력사", "협력업체", "파트너", "파트너사", "벤더",
                "조달", "구매", "납품", "공급", "발주", "수주", "계약",
                "상생", "상생협력", "동반성장", "win-win", "파트너십",
                
                # 🌐 글로벌 공급망
                "글로벌공급망", "해외공급망", "국제조달", "수출입", "무역",
                "공급망위기", "공급망리스크", "공급차질", "공급부족",
                "원자재", "부품", "소재", "핵심소재", "반도체", "배터리",
                
                # 📊 공급망 관리
                "공급망관리", "SCM", "품질관리", "품질보증", "QA", "QC",
                "납기", "납기관리", "재고", "재고관리", "물류", "유통",
                "디지털화", "디지털전환", "스마트팩토리", "자동화",
                
                # 🌱 지속가능 공급망
                "ESG공급망", "지속가능조달", "친환경조달", "그린공급망",
                "인권", "노동인권", "아동노동", "강제노동", "공정무역",
                "투명성", "추적가능성", "공급망실사", "due diligence"
            ],
            
            "에너지 효율 향상": [
                # ⚡ 기본 에너지 효율 키워드
                "에너지효율", "효율", "고효율", "절약", "절전", "에너지절약",
                "효율성", "효율개선", "효율향상", "성능", "성능개선",
                "최적화", "운영최적화", "에너지관리", "전력관리",
                
                # 🏭 산업 에너지 효율
                "공장효율", "설비효율", "생산효율", "발전효율", "전력효율",
                "변환효율", "전력변환", "손실", "전력손실", "손실감소",
                "열효율", "냉각효율", "시스템효율", "통합효율",
                
                # 🔧 기술적 개선
                "기술개발", "개선", "개량", "업그레이드", "modernization",
                "혁신", "기술혁신", "공정개선", "시스템개선", "설비개선",
                "스마트화", "디지털화", "자동화", "지능화", "AI도입",
                
                # 📊 성과/측정
                "에너지성과", "효율등급", "효율인증", "에너지라벨",
                "절감", "절감효과", "비용절감", "원가절감", "운영비절감",
                "ROI", "투자회수", "경제성", "수익성"
            ],
            
            "지역사회공헌": [
                # 🏘️ 기본 지역사회 키워드
                "지역사회", "지역", "지역경제", "지역발전", "지역상생",
                "사회공헌", "CSR", "공헌", "기여", "참여", "협력",
                "지역협력", "상생협력", "동반성장", "상생발전",
                
                # 💝 구체적 공헌 활동
                "기부", "후원", "장학금", "봉사", "자원봉사", "나눔",
                "사회봉사", "지역봉사", "환경봉사", "복지", "사회복지",
                "문화", "문화지원", "스포츠", "체육", "교육", "교육지원",
                
                # 👥 지역 이해관계자
                "주민", "지역주민", "시민", "지역시민", "자치단체",
                "지방정부", "지자체", "시청", "군청", "구청", "동사무소",
                "지역기관", "지역단체", "시민단체", "NGO", "NPO",
                
                # 💼 지역 경제/고용
                "일자리", "지역일자리", "고용창출", "취업", "창업지원",
                "중소기업", "지역기업", "협력업체", "지역상권", "상권활성화",
                "투자", "지역투자", "시설투자", "인프라", "지역인프라"
            ],
            
            "용수관리": [
                # 💧 기본 용수/물 관리 키워드
                "용수", "물", "수자원", "급수", "급수시설", "상수도",
                "공업용수", "냉각수", "보일러용수", "용수공급", "물공급",
                "수질", "수질관리", "수질개선", "수질오염", "오염방지",
                
                # 🏭 산업 용수 (발전소 특화)
                "냉각수", "순환냉각수", "냉각탑", "복수기", "취수", "방류",
                "온배수", "열오염", "수온", "수온상승", "생태계영향",
                "어류", "해양생물", "해양생태계", "담수생태계",
                
                # 🔄 용수 처리/재활용
                "폐수", "폐수처리", "하수처리", "정수", "정수처리",
                "재활용", "재이용", "물재활용", "중수도", "빗물활용",
                "절약", "물절약", "절수", "용수절약", "효율적사용",
                
                # 📋 관련 규제/기준
                "환경기준", "배출기준", "수질기준", "허가", "취수허가",
                "방류허가", "환경영향평가", "모니터링", "수질검사",
                "규제", "환경규제", "물환경보전법", "수질보전"
            ]
        }
        
        # 🎯 회사별 특화 키워드 (간단하고 광범위하게)
        self.company_keywords = {
            "두산퓨얼셀": [
                # 🏢 기업 식별
                "두산", "두산퓨얼셀", "doosan", "fuel cell", "DFCL",
                
                # ⚡ 핵심 사업 (간단한 용어)
                "연료전지", "수소", "수소연료전지", "수소발전", "수소경제",
                "그린수소", "청정수소", "수소사업", "수소기술", "연료전지사업",
                "발전", "발전사업", "전력", "전력생산", "에너지", "청정에너지",
                
                # 🔋 제품/기술 (일반적 표현)
                "연료전지시스템", "발전시스템", "에너지시스템", "전력시스템",
                "가정용", "건물용", "발전용", "대용량", "분산전원", "마이크로그리드",
                "효율", "고효율", "성능", "내구성", "수명", "안정성",
                
                # 🌱 관련 분야
                "친환경", "청정", "무공해", "제로배출", "탄소중립", "ESG",
                "신재생에너지", "재생에너지", "에너지전환", "그린뉴딜"
            ],
            
            "LS ELECTRIC": [
                # 🏢 기업 식별
                "LS", "LS일렉트릭", "LS ELECTRIC", "엘에스", "엘에스일렉트릭",
                
                # ⚡ 핵심 사업 (간단한 용어)
                "전력", "전력기기", "전력설비", "전기", "전기설비",
                "변압기", "차단기", "개폐기", "배전", "송전", "수배전",
                "전력변환", "인버터", "컨버터", "ESS", "에너지저장",
                
                # 🔧 제품/기술 (일반적 표현)
                "전력시스템", "배전시스템", "제어시스템", "자동화시스템",
                "스마트그리드", "그리드", "전력망", "전력계통", "계통연계",
                "반도체", "파워반도체", "전력용반도체", "모듈", "전자부품",
                
                # 🏭 적용 분야
                "산업자동화", "공장자동화", "빌딩자동화", "철도", "전철",
                "신재생에너지", "태양광", "풍력", "배터리", "전기차", "EV",
                "데이터센터", "통신", "IT", "스마트팩토리"
            ],
            
            "한국중부발전": [
                # 🏢 기업 식별  
                "중부발전", "한국중부발전", "KOMIPO", "중발", "중부발전소",
                
                # ⚡ 핵심 사업 (간단한 용어)
                "발전", "발전소", "전력", "전력생산", "전력공급", "전기",
                "화력발전", "석탄화력", "LNG발전", "가스발전", "복합화력",
                "열병합", "집단에너지", "발전사업", "전력사업",
                
                # 🌱 친환경 전환
                "신재생에너지", "재생에너지", "태양광", "풍력", "연료전지",
                "ESS", "에너지저장", "그린수소", "수소발전", "암모니아발전",
                "탄소중립", "친환경", "청정발전", "에너지전환", "탈석탄",
                
                # 🏭 시설/설비 (일반적 표현)
                "발전설비", "발전기", "터빈", "보일러", "변압기", "송전",
                "발전단지", "발전소부지", "시설", "설비", "인프라",
                "정비", "보수", "점검", "개선", "업그레이드", "현대화",
                
                # 🌍 환경/안전
                "환경", "환경설비", "대기오염", "미세먼지", "배출", "배출저감",
                "환경개선", "환경투자", "안전", "안전관리", "사고", "예방",
                "온실가스", "이산화탄소", "질소산화물", "황산화물",
                
                # 👥 지역/사회
                "지역", "지역사회", "상생", "지역상생", "주민", "지역주민",
                "지역경제", "일자리", "고용", "투자", "협력", "상생협력"
            ]
        }
        
        # 🎯 일반적인 ESG/비즈니스 키워드 추가 (광범위한 매칭용)
        self.general_esg_keywords = [
            # 환경 (E)
            "환경", "친환경", "그린", "청정", "에코", "지속가능", "ESG",
            "기후", "탄소", "온실가스", "배출", "오염", "절약", "효율",
            "재생에너지", "신재생", "에너지", "전력", "발전", "수소", "배터리",
            
            # 사회 (S)  
            "안전", "사고", "재해", "고용", "일자리", "교육", "훈련",
            "지역사회", "상생", "협력", "기부", "봉사", "공헌", "복지",
            "인권", "다양성", "포용", "상생", "동반성장",
            
            # 거버넌스 (G)
            "거버넌스", "윤리", "투명", "컴플라이언스", "준법", "반부패",
            "이사회", "감사", "내부통제", "리스크", "위험관리"
        ]
        
        # 🔧 가중치 설정 (매칭률 향상을 위해 조정)
        self.weights = {
            'title_match': 3.0,          # 제목 매칭 (적당히 높게)
            'content_match': 1.5,        # 본문 매칭 (기본값)
            'company_exact_match': 5.0,  # 회사명 정확 매칭 (매우 높게)
            'company_partial_match': 2.0, # 회사명 부분 매칭
            'keyword_exact_match': 2.0,  # 키워드 정확 매칭
            'keyword_partial_match': 1.0, # 키워드 부분 매칭 (추가)
            'general_esg_match': 0.8,    # 일반 ESG 키워드 매칭 (낮게)
            'sentiment_positive': 1.2,   # 긍정 sentiment 가중치
            'sentiment_negative': 0.9,   # 부정 sentiment 가중치
            'recent_news': 1.3,          # 최근 뉴스 가중치
            'keyword_density': 1.8,      # 키워드 밀도 가중치
            'multiple_keyword_bonus': 1.5 # 복수 키워드 매칭 보너스 (추가)
        }
        
        # 🎯 관련성 임계값 대폭 하향 조정 (매칭률 향상)
        self.relevance_threshold = 0.1  # 0.3 → 0.1로 대폭 하향
    
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
        """🎯 대폭 개선된 기사 관련성 점수 계산 (광범위한 매칭)"""
        title = article.get('title', '')
        content = article.get('content', '') or article.get('summary', '') or article.get('description', '')
        sentiment = article.get('sentiment', 'neutral')
        published_at = article.get('published_at', '')
        
        total_score = 0.0
        
        # 1. 🏢 회사명 매칭 (대폭 강화)
        company_score = self._calculate_company_relevance(title, content, company_name)
        total_score += company_score
        
        # 2. 🎯 토픽 키워드 매칭
        keyword_score = self._calculate_keyword_relevance(title, content, keywords)
        total_score += keyword_score
        
        # 3. 🌍 일반 ESG 키워드 매칭 (기본적인 ESG 관련성)
        esg_score = self._calculate_esg_relevance(title, content)
        total_score += esg_score
        
        # 4. 💯 복수 키워드 매칭 보너스
        multiple_keyword_bonus = self._calculate_multiple_keyword_bonus(title, content, keywords)
        total_score += multiple_keyword_bonus
        
        # 5. 😊 sentiment 가중치 적용
        if sentiment == 'positive':
            total_score *= self.weights['sentiment_positive']
        elif sentiment == 'negative':
            total_score *= self.weights['sentiment_negative']
        
        # 6. 📅 최근성 가중치 적용
        if self._is_recent_news(published_at):
            total_score *= self.weights['recent_news']
        
        # 7. 📊 키워드 밀도 가중치
        keyword_density = self._calculate_keyword_density(title + ' ' + content, keywords)
        total_score += keyword_density * self.weights['keyword_density']
        
        return max(0.0, total_score)  # 음수 방지
    
    def _calculate_company_relevance(self, title: str, content: str, company_name: str) -> float:
        """🏢 회사명 관련성 점수 계산 (강화된 버전)"""
        if not company_name:
            return 0.0
        
        score = 0.0
        full_text = (title + ' ' + content).lower()
        
        # 회사별 다양한 표현 정의
        company_variations = {
            "두산퓨얼셀": ["두산", "두산퓨얼셀", "doosan", "fuel cell", "dfcl", "퓨얼셀", "연료전지"],
            "LS ELECTRIC": ["ls", "ls일렉트릭", "ls electric", "엘에스", "엘에스일렉트릭", "ls전기"],
            "한국중부발전": ["중부발전", "한국중부발전", "komipo", "중발", "중부발전소", "한전중부발전"]
        }
        
        # 1. 정확한 회사명 매칭
        if company_name.lower() in full_text:
            score += self.weights['company_exact_match']
        
        # 2. 회사 변형 표현 매칭
        if company_name in company_variations:
            for variation in company_variations[company_name]:
                if variation.lower() in full_text:
                    score += self.weights['company_partial_match']
                    break  # 중복 점수 방지
        
        # 3. 제목에서 회사명 매칭 시 추가 보너스
        title_lower = title.lower()
        if company_name.lower() in title_lower:
            score += self.weights['company_exact_match'] * 0.5  # 추가 보너스
        
        return score
    
    def _calculate_keyword_relevance(self, title: str, content: str, keywords: List[str]) -> float:
        """🎯 키워드 관련성 점수 계산"""
        if not keywords:
            return 0.0
        
        score = 0.0
        
        # 1. 제목에서 키워드 매칭
        title_exact = self._count_exact_keyword_matches(title, keywords)
        title_partial = self._count_partial_keyword_matches(title, keywords)
        score += title_exact * self.weights['title_match'] * self.weights['keyword_exact_match']
        score += title_partial * self.weights['title_match'] * self.weights['keyword_partial_match']
        
        # 2. 본문에서 키워드 매칭
        content_exact = self._count_exact_keyword_matches(content, keywords)
        content_partial = self._count_partial_keyword_matches(content, keywords)
        score += content_exact * self.weights['content_match'] * self.weights['keyword_exact_match']
        score += content_partial * self.weights['content_match'] * self.weights['keyword_partial_match']
        
        return score
    
    def _calculate_esg_relevance(self, title: str, content: str) -> float:
        """🌍 일반 ESG 키워드 관련성 점수 계산"""
        if not hasattr(self, 'general_esg_keywords') or not self.general_esg_keywords:
            return 0.0
        
        full_text = (title + ' ' + content).lower()
        esg_matches = 0
        
        for esg_keyword in self.general_esg_keywords:
            if esg_keyword.lower() in full_text:
                esg_matches += 1
        
        return esg_matches * self.weights['general_esg_match']
    
    def _calculate_multiple_keyword_bonus(self, title: str, content: str, keywords: List[str]) -> float:
        """💯 복수 키워드 매칭 보너스 계산"""
        if not keywords or len(keywords) < 2:
            return 0.0
        
        full_text = (title + ' ' + content).lower()
        matched_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in full_text:
                matched_keywords.append(keyword)
        
        # 복수 키워드 매칭 시 보너스 점수
        if len(matched_keywords) >= 2:
            bonus_multiplier = min(len(matched_keywords) / len(keywords), 0.5)  # 최대 50% 보너스
            return bonus_multiplier * self.weights['multiple_keyword_bonus']
        
        return 0.0
    
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