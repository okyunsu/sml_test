# Material Assessment Service

중대성 평가 동향 분석 및 업데이트 제안 서비스 (MVP)

## 🚀 주요 기능

### 💼 회사별 중대성 분석 (MVP)
- **두산퓨얼셀**: 2024년 SR 보고서 기반 연료전지 및 신재생에너지 기업 중대성 평가 분석
- **LS ELECTRIC**: 2024년 SR 보고서 기반 전력 및 자동화 솔루션 기업 중대성 평가 분석
- **한국중부발전**: 2024년 SR 보고서 기반 화력발전 및 신재생에너지 전환 기업 중대성 평가 분석
- **하이브리드 뉴스 분석**: 기업별 뉴스 + 산업군 뉴스를 조합한 종합 분석
- **2025년 전망**: 2024년 기준 데이터로 2025년 중대성 평가 변화 예측
- **평가 비교**: 연도별 중대성 평가 비교 분석

### 🏭 산업별 중대성 분석 (MVP)
- **신재생에너지 산업**: 태양광, 풍력, 연료전지 등 신재생에너지 산업 중대성 이슈 분석
- **산업 트렌드**: 수소 에너지, 에너지 저장 시스템(ESS) 등 주요 트렌드 분석
- **SASB 매핑**: 신재생에너지 산업 주요 SASB 이슈 식별 및 매핑

### 📊 기본 관리 기능
- **2024년 SR 보고서 기반**: materiality 폴더의 실제 SR 보고서 키워드 활용
- **SASB 매핑 시스템**: 중대성 평가 토픽과 SASB 이슈 자동 매핑
- **실시간 데이터 조회**: 파일 기반 실시간 중대성 평가 데이터 제공

## 🏢 지원 기업 (MVP)

### 두산퓨얼셀
- **산업**: 신재생에너지 (연료전지)
- **데이터**: `materiality/doosan.txt` (2024년 SR 보고서에서 추출)
- **주요 토픽**: 기후변화 대응, 순환경제, 제품 환경영향 저감, 사업장 안전보건, 반부패 윤리경영 강화 등

### LS ELECTRIC
- **산업**: 신재생에너지 (전력/자동화)
- **데이터**: `materiality/ls.txt` (2024년 SR 보고서에서 추출)
- **주요 토픽**: 기후변화 대응, 공급망 관리 및 상생경영, 제품 에너지 효율 향상, 안전한 작업환경 등

### 한국중부발전
- **산업**: 발전 (화력발전/신재생에너지 전환)
- **데이터**: `materiality/komipo.txt` (2024년 SR 보고서에서 추출)
- **주요 토픽**: 기후변화 대응 및 온실가스 감축, 신재생에너지 전환 및 확대, 안전보건 관리체계 구축, 지역사회 상생 및 발전 등

## 🏭 지원 산업 (MVP)

### 신재생에너지
- **설명**: 태양광, 풍력, 연료전지 등 신재생에너지 산업
- **주요 SASB 토픽**: 기후변화 대응, 환경 영향, 에너지 효율, 기술 혁신, 안전, 규제 준수
- **관련 기업**: 두산퓨얼셀, LS ELECTRIC

## 🔍 뉴스 분석 방식 (하이브리드 접근법)

### 키워드 조합 전략
```
검색 키워드 = [
  🏢 기업명 (두산퓨얼셀, LS ELECTRIC)
  + 📋 토픽별 키워드 (기후변화, 탄소중립, ESG 등)
  + 🔧 회사 특화 키워드 (연료전지, 수소, 전력기기, ESS 등) 
  + 🏭 SASB 산업 키워드 (신재생에너지, 청정에너지 등)
]
```

### 데이터 수집 범위
1. **🏢 기업 중심 뉴스** (Primary): 두산퓨얼셀, LS ELECTRIC이 직접 언급된 뉴스
2. **🏭 산업군 뉴스** (Secondary): 신재생에너지 산업 관련 뉴스
3. **🔗 토픽별 확장**: 각 중대성 토픽 특화 키워드로 관련 뉴스 필터링

## 📡 API 엔드포인트

### 🎨 기본 관리 API

#### 1. 헬스체크
```bash
GET /api/v1/materiality/health
```

#### 2. 지원 기업 목록 조회
```bash
GET /api/v1/materiality/companies
```
**응답 예시:**
```json
{
  "status": "success",
  "total_companies": 2,
  "companies": [
    {
      "company_name": "두산퓨얼셀",
      "has_assessment": true,
      "available_years": [2024, 2025]
    },
    {
      "company_name": "LS ELECTRIC", 
      "has_assessment": true,
      "available_years": [2024, 2025]
    }
  ]
}
```

#### 3. 기업별 중대성 평가 조회
```bash
GET /api/v1/materiality/companies/{company_name}/assessment/{year}
```

### 💼 회사별 중대성 분석 API

#### 1. 회사별 중대성 평가 분석 (핵심 기능)
```bash
POST /api/v1/materiality/companies/{company_name}/analyze
```

**Query Parameters:**
- `year`: 분석 연도 (기본값: 2025)
- `include_news`: 뉴스 분석 포함 여부 (기본값: true)  
- `max_articles`: 분석할 최대 뉴스 수 (기본값: 100)

**예시:**
```bash
curl -X POST "http://localhost:8004/api/v1/materiality/companies/두산퓨얼셀/analyze?year=2025&include_news=true&max_articles=100"
```

**분석 로직:**
- **Base Year**: 2024 (SR 보고서 데이터)
- **Analysis Year**: 2025 (전망 분석)
- **키워드 조합**: 두산퓨얼셀 + 연료전지 + 수소 + 기후변화 + 신재생에너지 etc.

#### 2. 회사별 중대성 평가 비교
```bash
GET /api/v1/materiality/companies/{company_name}/compare?year1=2024&year2=2025
```

### 🏭 산업별 중대성 분석 API

#### 1. 산업별 중대성 이슈 분석
```bash
POST /api/v1/materiality/industries/{industry}/analyze
```

**Query Parameters:**
- `year`: 분석 연도 (기본값: 2025)
- `max_articles`: 분석할 최대 뉴스 수 (기본값: 200)
- `include_sasb_mapping`: SASB 매핑 포함 여부 (기본값: true)

**예시:**
```bash
curl -X POST "http://localhost:8004/api/v1/materiality/industries/신재생에너지/analyze?year=2025&max_articles=200"
```

#### 2. 지원 산업 목록 조회
```bash
GET /api/v1/materiality/industries
```

## 🛠️ 기술 스택

- **Framework**: FastAPI
- **Language**: Python 3.9+
- **Database**: File-based (2024년 실제 SR 보고서 텍스트 파일)
- **External Services**: Gateway, SASB Service
- **Port**: 8004
- **Containerization**: Docker

## 📦 프로젝트 구조

```
material-service/
├── app/
│   ├── api/
│   │   └── materiality_router.py          # API 라우터 (기본값: 2025년 분석)
│   ├── domain/
│   │   ├── model/
│   │   │   └── materiality_dto.py         # 데이터 모델
│   │   └── service/
│   │       ├── materiality_analysis_service.py     # 회사별 중대성 분석 (핵심)
│   │       ├── materiality_update_engine.py        # 업데이트 엔진
│   │       ├── news_analysis_engine.py              # 뉴스 분석 엔진 (하이브리드)
│   │       ├── industry_analysis_service.py        # 산업별 중대성 분석
│   │       ├── materiality_file_service.py         # 파일 관리 (2024 SR 데이터)
│   │       ├── materiality_mapping_service.py      # SASB 매핑
│   │       └── materiality_recommendation_service.py # 추천 시스템
│   ├── core/
│   │   ├── gateway_client.py              # Gateway 클라이언트 (sasb-service 연동)
│   │   └── exceptions.py                  # 예외 처리
│   ├── config/
│   │   └── settings.py                    # 설정 (포트: 8004)
│   └── main.py                            # FastAPI 애플리케이션
├── materiality/
│   ├── doosan.txt                         # 두산퓨얼셀 2024년 SR 보고서 키워드
│   └── ls.txt                             # LS ELECTRIC 2024년 SR 보고서 키워드
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🚀 실행 방법

### 1. 로컬 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### 2. Docker 실행
```bash
# 이미지 빌드
docker build -t material-service .

# 컨테이너 실행
docker run -p 8004:8004 material-service
```

### 3. Docker Compose 실행
```bash
# 전체 서비스 실행 (Gateway + SASB Service + Material Service)
docker-compose up -d
```

## 🔧 환경 변수

```bash
# Gateway 설정 (필수)
GATEWAY_URL=http://localhost:8080

# 포트 설정
PORT=8004

# 로그 레벨
LOG_LEVEL=INFO

# SASB Service 연동
SASB_SERVICE_URL=http://localhost:8003
```

## 📄 API 응답 예시

### 회사별 중대성 분석 결과
```json
{
  "analysis_metadata": {
    "company_name": "두산퓨얼셀",
    "base_year": 2024,
    "analysis_year": 2025,
    "analysis_date": "2025-01-15T10:30:00Z",
    "data_source": "2024년 SR 보고서 + 뉴스 분석",
    "disclaimer": "뉴스 분석 결과는 참고용이며, 실제 중대성 평가는 이해관계자 의견을 종합하여 수행해야 합니다."
  },
  "base_assessment": {
    "year": 2024,
    "source": "SR 보고서",
    "topics_count": 10,
    "key_topics": ["기후변화 대응", "순환경제", "제품 환경영향 저감"]
  },
  "news_analysis": {
    "total_articles": 85,
    "analysis_period": "2024년 기준 2025년 전망",
    "search_strategy": "기업명 + 특화키워드 + 산업키워드 조합",
    "key_changes": [
      {
        "topic": "기후변화 대응",
        "change_type": "increased_importance",
        "confidence": 0.8,
        "rationale": "연료전지 + 탄소중립 관련 뉴스 급증"
      }
    ]
  },
  "recommendations": [
    {
      "action": "수소 에너지 관련 이슈 우선순위 상향 검토",
      "confidence": 0.85,
      "supporting_evidence": "뉴스 멘션 45건, 정책 변화 반영 필요"
    }
  ]
}
```

### 산업별 중대성 분석 결과
```json
{
  "analysis_metadata": {
    "industry": "신재생에너지",
    "analysis_year": 2025,
    "analysis_date": "2025-01-15T10:30:00Z",
    "companies_analyzed": ["두산퓨얼셀", "LS ELECTRIC"],
    "disclaimer": "산업 분석 결과는 참고용입니다."
  },
  "industry_info": {
    "description": "태양광, 풍력, 연료전지 등 신재생에너지 산업",
    "key_sasb_topics": ["기후변화 대응", "환경 영향", "에너지 효율"],
    "related_companies": ["두산퓨얼셀", "LS ELECTRIC"]
  },
  "materiality_analysis": {
    "key_issues": [
      {
        "issue_name": "기후변화 대응",
        "mention_count": 45,
        "relevance_score": 0.65,
        "trend": "increasing"
      }
    ],
    "emerging_issues": [
      {
        "issue_name": "수소 경제",
        "mention_count": 12,
        "trend": "emerging",
        "impact_level": "high"
      }
    ]
  },
  "trend_analysis": {
    "key_trends": [
      {
        "trend_name": "수소 에너지 확산",
        "trend_direction": "increasing",
        "impact_level": "high",
        "companies_affected": ["두산퓨얼셀"]
      }
    ]
  }
}
```

## ⚠️ 주의사항 및 제한사항

### MVP 범위
1. **지원 기업**: 두산퓨얼셀, LS ELECTRIC 2개 기업만 지원
2. **지원 산업**: 신재생에너지 산업만 지원
3. **데이터 기준**: 2024년 SR 보고서 실제 키워드 기반
4. **분석 연도**: 기본적으로 2025년 전망 분석

### 분석 결과 활용 시 주의사항
1. **참고용 분석**: 뉴스 분석 결과는 참고용이며, 실제 중대성 평가는 다양한 이해관계자 의견을 종합하여 수행
2. **Gateway 의존성**: SASB 서비스와의 연동을 위해 Gateway 서비스 필수
3. **데이터 제한**: 파일 기반 데이터 관리로 확장성 제한
4. **뉴스 범위**: 한국어 뉴스 데이터 기반 분석

### 기술적 제약사항
- 파일 기반 데이터베이스 (확장성 제한)
- 정적 키워드 매핑 (동적 학습 미지원)
- 단일 언어 지원 (한국어만)

## 🔮 향후 개발 계획

### Phase 2 (확장 계획)
1. **기업 확장**: 더 많은 기업 지원 (삼성SDI, SK이노베이션 등)
2. **산업 확장**: 다양한 산업 분석 지원 (IT, 금융, 제조업 등)
3. **다년도 데이터**: SR 보고서 이력 데이터 활용
4. **실시간 업데이트**: 뉴스 크롤링 자동화

### Phase 3 (고도화)
1. **데이터베이스 연동**: 파일 기반에서 데이터베이스로 전환
2. **AI 분석 고도화**: 머신러닝 기반 예측 모델 도입
3. **사용자 인터페이스**: 웹 기반 대시보드 제공
4. **국제 표준 지원**: GRI, TCFD 등 다양한 ESG 표준 지원

## 📊 서비스 아키텍처

```
[Client] 
    ↓
[Material Service:8004]
    ↓
[Gateway:8080]
    ↓
[SASB Service:8003] → [뉴스 데이터]
    ↑
[Redis Cache] [News DB]
```

### 데이터 플로우
```
1. 2024년 SR 보고서 키워드 로드 (Base Assessment)
    ↓
2. 하이브리드 키워드 생성 (기업 + 토픽 + 산업)
    ↓  
3. SASB Service를 통한 뉴스 수집
    ↓
4. 뉴스 관련성 분석 및 점수 계산
    ↓
5. 2025년 중대성 평가 변화 예측 및 제안
```

---

## 💡 Quick Start

```bash
# 1. 서비스 실행
docker-compose up -d

# 2. API 문서 확인  
open http://localhost:8004/docs

# 3. 두산퓨얼셀 분석 예시
curl -X POST "http://localhost:8004/api/v1/materiality/companies/두산퓨얼셀/analyze?year=2025"

# 4. 산업 분석 예시
curl -X POST "http://localhost:8004/api/v1/materiality/industries/신재생에너지/analyze"
```

**🎯 핵심 가치**: 실제 2024년 SR 보고서 데이터를 기반으로 2025년 중대성 평가 변화를 뉴스 분석을 통해 예측하고 실무진에게 구체적인 업데이트 제안을 제공합니다. 