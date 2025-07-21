# Material Assessment Service

중대성 평가 동향 분석 및 업데이트 제안 서비스 (MVP)

## 🚀 주요 기능

### 💼 회사별 중대성 분석
- **두산퓨얼셀**: 연료전지 및 신재생에너지 기업 중대성 평가 분석
- **LS ELECTRIC**: 전력 및 자동화 솔루션 기업 중대성 평가 분석
- **뉴스 기반 변화 분석**: sasb-service 연동을 통한 뉴스 기반 중대성 평가 변화 분석
- **평가 비교**: 연도별 중대성 평가 비교 분석

### 🏭 산업별 중대성 분석
- **신재생에너지 산업**: 태양광, 풍력, 연료전지 등 신재생에너지 산업 중대성 이슈 분석
- **산업 트렌드**: 수소 에너지, 에너지 저장 시스템(ESS) 등 주요 트렌드 분석
- **SASB 매핑**: 신재생에너지 산업 주요 SASB 이슈 식별 및 매핑

### 📊 기본 관리 기능
- **중대성 평가 파일 관리**: materiality 폴더 기반 파일 시스템
- **SASB 매핑 시스템**: 중대성 평가 토픽과 SASB 이슈 자동 매핑
- **실시간 데이터 조회**: 파일 기반 실시간 중대성 평가 데이터 제공

## 🏢 지원 기업 (MVP)

### 두산퓨얼셀
- **산업**: 신재생에너지 (연료전지)
- **데이터**: `materiality/doosan.txt`
- **주요 토픽**: 기후변화 대응, 기술 혁신, 안전, 환경 영향 등

### LS ELECTRIC
- **산업**: 신재생에너지 (전력/자동화)
- **데이터**: `materiality/ls.txt`
- **주요 토픽**: 기후변화 대응, 공급망 관리, 에너지 효율 등

## 🏭 지원 산업 (MVP)

### 신재생에너지
- **설명**: 태양광, 풍력, 연료전지 등 신재생에너지 산업
- **주요 SASB 토픽**: 기후변화 대응, 환경 영향, 에너지 효율, 기술 혁신, 안전, 규제 준수
- **관련 기업**: 두산퓨얼셀, LS ELECTRIC

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

#### 3. 기업별 중대성 평가 조회
```bash
GET /api/v1/materiality/companies/{company_name}/assessment/{year}
```

### 💼 회사별 중대성 분석 API

#### 1. 회사별 중대성 평가 분석
```bash
POST /api/v1/materiality/companies/{company_name}/analyze
```

**Query Parameters:**
- `year`: 분석 연도 (기본값: 2024)
- `include_news`: 뉴스 분석 포함 여부 (기본값: true)
- `max_articles`: 분석할 최대 뉴스 수 (기본값: 100)

**예시:**
```bash
curl -X POST "http://localhost:8000/api/v1/materiality/companies/두산퓨얼셀/analyze?year=2024&include_news=true&max_articles=100"
```

#### 2. 회사별 중대성 평가 비교
```bash
GET /api/v1/materiality/companies/{company_name}/compare?year1=2023&year2=2024
```

### 🏭 산업별 중대성 분석 API

#### 1. 산업별 중대성 이슈 분석
```bash
POST /api/v1/materiality/industries/{industry}/analyze
```

**Query Parameters:**
- `year`: 분석 연도 (기본값: 2024)
- `max_articles`: 분석할 최대 뉴스 수 (기본값: 100)
- `include_sasb_mapping`: SASB 매핑 포함 여부 (기본값: true)

**예시:**
```bash
curl -X POST "http://localhost:8000/api/v1/materiality/industries/신재생에너지/analyze?year=2024&max_articles=100"
```

#### 2. 지원 산업 목록 조회
```bash
GET /api/v1/materiality/industries
```

## 🛠️ 기술 스택

- **Framework**: FastAPI
- **Language**: Python 3.9+
- **Database**: File-based (텍스트 파일)
- **External Services**: Gateway, SASB Service
- **Containerization**: Docker

## 📦 프로젝트 구조

```
material-service/
├── app/
│   ├── api/
│   │   └── materiality_router.py          # API 라우터
│   ├── domain/
│   │   ├── controller/
│   │   ├── model/
│   │   │   └── materiality_dto.py         # 데이터 모델
│   │   └── service/
│   │       ├── materiality_analysis_service.py    # 회사별 중대성 분석
│   │       ├── industry_analysis_service.py       # 산업별 중대성 분석
│   │       ├── materiality_file_service.py        # 파일 관리
│   │       └── materiality_mapping_service.py     # SASB 매핑
│   ├── core/
│   │   └── gateway_client.py              # Gateway 클라이언트
│   └── main.py
├── materiality/
│   ├── doosan.txt                         # 두산퓨얼셀 중대성 평가
│   └── ls.txt                             # LS ELECTRIC 중대성 평가
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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Docker 실행
```bash
# 이미지 빌드
docker build -t material-service .

# 컨테이너 실행
docker run -p 8000:8000 material-service
```

### 3. Docker Compose 실행
```bash
# 전체 서비스 실행
docker-compose up -d
```

## 🔧 환경 변수

```bash
# Gateway 설정
GATEWAY_URL=http://localhost:8080

# 로그 레벨
LOG_LEVEL=INFO
```

## 📄 API 응답 예시

### 회사별 중대성 분석 결과
```json
{
  "analysis_metadata": {
    "company_name": "두산퓨얼셀",
    "analysis_year": 2024,
    "analysis_date": "2024-01-15T10:30:00Z",
    "disclaimer": "뉴스 분석 결과는 참고용입니다."
  },
  "news_analysis": {
    "total_articles": 85,
    "analysis_period": "2024년",
    "key_changes": [
      {
        "topic": "기후변화 대응",
        "change_type": "increased_importance",
        "confidence": 0.8
      }
    ]
  },
  "recommendations": [
    "수소 에너지 관련 이슈에 대한 우선적 관리가 필요합니다."
  ]
}
```

### 산업별 중대성 분석 결과
```json
{
  "analysis_metadata": {
    "industry": "신재생에너지",
    "analysis_year": 2024,
    "analysis_date": "2024-01-15T10:30:00Z",
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
        "relevance_score": 0.65
      }
    ],
    "emerging_issues": [
      {
        "issue_name": "에너지 효율",
        "mention_count": 2,
        "trend": "emerging"
      }
    ]
  },
  "trend_analysis": {
    "key_trends": [
      {
        "trend_name": "수소 에너지 확산",
        "trend_direction": "increasing",
        "impact_level": "high"
      }
    ]
  }
}
```

## ⚠️ 주의사항

1. **MVP 범위**: 현재 두산퓨얼셀, LS ELECTRIC 2개 회사와 신재생에너지 산업만 지원
2. **참고용 분석**: 뉴스 분석 결과는 참고용이며, 실제 중대성 평가는 다양한 이해관계자 의견을 종합하여 수행
3. **Gateway 의존성**: SASB 서비스와의 연동을 위해 Gateway 서비스 필요
4. **데이터 제한**: 파일 기반 데이터 관리로 확장성 제한

## 🔮 향후 개발 계획

1. **기업 확장**: 더 많은 기업 지원
2. **산업 확장**: 다양한 산업 분석 지원
3. **데이터베이스 연동**: 파일 기반에서 데이터베이스로 전환
4. **고도화된 분석**: 머신러닝 기반 분석 도입
5. **사용자 인터페이스**: 웹 기반 대시보드 제공 