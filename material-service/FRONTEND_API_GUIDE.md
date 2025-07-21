# Material Service API Guide for Frontend

프론트엔드 연결을 위한 Material Assessment Service API 가이드

## 🌐 기본 설정

### Base URL
```
Gateway를 통한 접근: http://localhost:8080/gateway/v1/material
Direct 접근 (개발용): http://localhost:8004
```

### 헤더 설정
```javascript
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

---

## 📚 API 엔드포인트 목록

### 🎯 1. 기본 정보 조회 API (GET)

#### 1.1 서비스 상태 확인
```http
GET /gateway/v1/material/api/v1/materiality/health
```
**용도**: 서비스 상태 확인 (헬스체크)  
**응답 예시**:
```json
{
  "status": "healthy",
  "service": "material-assessment-service", 
  "version": "2.0.0"
}
```

#### 1.2 지원 기업 목록 조회
```http
GET /gateway/v1/material/api/v1/materiality/companies
```
**용도**: 분석 가능한 기업 목록 조회  
**응답 예시**:
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
**프론트엔드 활용**: 드롭다운, 기업 선택 UI

#### 1.3 특정 기업 중대성 평가 조회
```http
GET /gateway/v1/material/api/v1/materiality/companies/{company_name}/assessment/{year}
```
**매개변수**:
- `company_name`: 기업명 (예: "두산퓨얼셀", "LS ELECTRIC")
- `year`: 연도 (예: 2024)

**예시 요청**:
```http
GET /gateway/v1/material/api/v1/materiality/companies/두산퓨얼셀/assessment/2024
```

**응답 예시**:
```json
{
  "assessment_id": "두산퓨얼셀_2024_20241201_143052",
  "company_name": "두산퓨얼셀",
  "year": 2024,
  "upload_date": "2024-12-01T14:30:52.123456",
  "topics": [
    {
      "topic_name": "기후변화 대응",
      "priority": 1,
      "year": 2024,
      "company_name": "두산퓨얼셀",
      "sasb_mapping": "E-GHG"
    },
    {
      "topic_name": "순환경제",
      "priority": 2,
      "year": 2024,
      "company_name": "두산퓨얼셀", 
      "sasb_mapping": "E-WASTE"
    }
  ]
}
```
**프론트엔드 활용**: 기준 데이터 표시, 차트 기본값

#### 1.4 지원 산업 목록 조회
```http
GET /gateway/v1/material/api/v1/materiality/industries
```
**용도**: 산업별 분석 가능한 산업 목록 조회  
**응답 예시**:
```json
{
  "status": "success",
  "total_industries": 1,
  "industries": [
    {
      "industry_name": "신재생에너지",
      "description": "태양광, 풍력, 연료전지 등 신재생에너지 산업",
      "key_sasb_topics": ["기후변화 대응", "환경 영향", "에너지 효율"],
      "related_companies": ["두산퓨얼셀", "LS ELECTRIC"]
    }
  ]
}
```

#### 1.5 기업별 중대성 평가 비교
```http
GET /gateway/v1/material/api/v1/materiality/companies/{company_name}/compare?year1={year1}&year2={year2}
```
**매개변수**:
- `company_name`: 기업명
- `year1`: 기준 연도 (Query Parameter)
- `year2`: 비교 연도 (Query Parameter)

**예시 요청**:
```http
GET /gateway/v1/material/api/v1/materiality/companies/두산퓨얼셀/compare?year1=2024&year2=2025
```

**응답 예시**:
```json
{
  "status": "success", 
  "company_name": "두산퓨얼셀",
  "comparison_period": "2024 vs 2025",
  "analysis_date": "2025-01-15T10:30:00.000Z",
  "comparison_summary": {
    "total_topics_year1": 10,
    "total_topics_year2": 12,
    "priority_changes": 3,
    "new_topics": 2,
    "removed_topics": 0
  },
  "detailed_comparison": {
    "priority_changes": [
      {
        "topic_name": "기후변화 대응",
        "previous_priority": 1,
        "current_priority": 1,
        "change": 0,
        "change_type": "unchanged"
      }
    ],
    "new_topics": ["수소 경제", "디지털 전환"],
    "removed_topics": []
  }
}
```
**프론트엔드 활용**: 변화 분석 차트, 비교 대시보드

---

### 🚀 2. 분석 실행 API (POST)

#### 2.1 기업별 중대성 분석 (핵심 기능)
```http
POST /gateway/v1/material/api/v1/materiality/companies/{company_name}/analyze
```
**매개변수**:
- `company_name`: 기업명 (Path Parameter)
- `year`: 분석 연도 (Query Parameter, 기본값: 2025)
- `include_news`: 뉴스 분석 포함 여부 (Query Parameter, 기본값: true)
- `max_articles`: 분석할 최대 뉴스 수 (Query Parameter, 기본값: 100)

**예시 요청**:
```http
POST /gateway/v1/material/api/v1/materiality/companies/두산퓨얼셀/analyze?year=2025&include_news=true&max_articles=100
```

**응답 예시**:
```json
{
  "analysis_metadata": {
    "company_name": "두산퓨얼셀",
    "base_year": 2024,
    "analysis_year": 2025,
    "analysis_date": "2025-01-15T10:30:00.000Z",
    "data_source": "2024년 SR 보고서 + 뉴스 분석",
    "disclaimer": "뉴스 분석 결과는 참고용입니다."
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
**프론트엔드 활용**: 메인 분석 결과 화면, 인사이트 대시보드

#### 2.2 산업별 중대성 분석
```http
POST /gateway/v1/material/api/v1/materiality/industries/{industry}/analyze
```
**매개변수**:
- `industry`: 산업명 (Path Parameter, 예: "신재생에너지")
- `year`: 분석 연도 (Query Parameter, 기본값: 2025)
- `max_articles`: 분석할 최대 뉴스 수 (Query Parameter, 기본값: 200)
- `include_sasb_mapping`: SASB 매핑 포함 여부 (Query Parameter, 기본값: true)

**예시 요청**:
```http
POST /gateway/v1/material/api/v1/materiality/industries/신재생에너지/analyze?year=2025&max_articles=200
```

**응답 예시**:
```json
{
  "analysis_metadata": {
    "industry": "신재생에너지",
    "analysis_year": 2025,
    "analysis_date": "2025-01-15T10:30:00.000Z",
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
**프론트엔드 활용**: 산업 인사이트 페이지, 트렌드 분석 차트

---

## 💻 프론트엔드 연동 예시 (JavaScript)

### 1. 기업 목록 조회
```javascript
async function getCompanies() {
  try {
    const response = await fetch('/gateway/v1/material/api/v1/materiality/companies', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.companies;
  } catch (error) {
    console.error('기업 목록 조회 실패:', error);
    throw error;
  }
}
```

### 2. 기업별 분석 실행
```javascript
async function analyzeCompany(companyName, options = {}) {
  const {
    year = 2025,
    includeNews = true,
    maxArticles = 100
  } = options;
  
  const params = new URLSearchParams({
    year: year.toString(),
    include_news: includeNews.toString(),
    max_articles: maxArticles.toString()
  });
  
  try {
    const response = await fetch(
      `/gateway/v1/material/api/v1/materiality/companies/${encodeURIComponent(companyName)}/analyze?${params}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const analysisResult = await response.json();
    return analysisResult;
  } catch (error) {
    console.error('기업 분석 실패:', error);
    throw error;
  }
}
```

### 3. 사용 예시
```javascript
// 페이지 로드시 기업 목록 조회
async function initializePage() {
  try {
    const companies = await getCompanies();
    populateCompanyDropdown(companies);
  } catch (error) {
    showErrorMessage('기업 목록을 불러올 수 없습니다.');
  }
}

// 분석 버튼 클릭시
async function handleAnalyzeClick() {
  const selectedCompany = document.getElementById('company-select').value;
  const analysisYear = document.getElementById('year-input').value || 2025;
  
  showLoadingSpinner();
  
  try {
    const result = await analyzeCompany(selectedCompany, {
      year: analysisYear,
      includeNews: true,
      maxArticles: 100
    });
    
    displayAnalysisResult(result);
  } catch (error) {
    showErrorMessage('분석 중 오류가 발생했습니다.');
  } finally {
    hideLoadingSpinner();
  }
}
```

---

## 🔧 에러 처리

### 일반적인 에러 응답 형태
```json
{
  "detail": "오류 메시지",
  "status_code": 400
}
```

### 주요 에러 코드
- **400**: 잘못된 요청 (매개변수 오류)
- **404**: 리소스 없음 (지원하지 않는 기업/산업)
- **500**: 서버 내부 오류

### 에러 처리 예시
```javascript
async function handleApiCall(apiCall) {
  try {
    const result = await apiCall();
    return result;
  } catch (error) {
    if (error.response) {
      // API 에러 응답
      const status = error.response.status;
      const detail = error.response.data?.detail || '알 수 없는 오류';
      
      switch (status) {
        case 404:
          showErrorMessage('지원하지 않는 기업 또는 산업입니다.');
          break;
        case 500:
          showErrorMessage('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
          break;
        default:
          showErrorMessage(`오류: ${detail}`);
      }
    } else {
      // 네트워크 에러 등
      showErrorMessage('네트워크 오류가 발생했습니다.');
    }
  }
}
```

---

## 📊 UI 구성 권장사항

### 1. 메인 대시보드
- **기업 선택 드롭다운**: `GET /companies`
- **분석 실행 버튼**: `POST /companies/{name}/analyze`
- **결과 표시 영역**: 분석 결과 시각화

### 2. 비교 분석 페이지
- **연도 선택 UI**: 2024 vs 2025
- **비교 차트**: `GET /companies/{name}/compare`
- **변화 요약**: priority_changes, new_topics

### 3. 산업 인사이트 페이지
- **산업 선택**: `GET /industries`
- **산업 분석**: `POST /industries/{industry}/analyze`
- **트렌드 시각화**: trend_analysis 데이터

### 4. 로딩 및 상태 관리
```javascript
// 분석 진행 상태 표시
const AnalysisStates = {
  IDLE: 'idle',
  LOADING: 'loading', 
  SUCCESS: 'success',
  ERROR: 'error'
};

function updateAnalysisState(state, message = '') {
  const statusElement = document.getElementById('analysis-status');
  statusElement.className = `status ${state}`;
  statusElement.textContent = message;
}
```

---

## 🎯 개발 팁

### 1. 캐싱 전략
- 기업 목록은 로컬 스토리지에 캐싱
- 분석 결과는 세션 스토리지에 임시 저장

### 2. 성능 최적화
- 분석 API는 시간이 오래 걸릴 수 있으므로 적절한 타임아웃 설정
- 로딩 상태 및 진행률 표시

### 3. 사용자 경험
- 분석 중 다른 기업 선택 방지
- 결과를 단계별로 표시 (메타데이터 → 뉴스 분석 → 추천사항)

### 4. 데이터 검증
```javascript
function validateAnalysisResult(result) {
  return result && 
         result.analysis_metadata && 
         result.recommendations && 
         Array.isArray(result.recommendations);
}
```

---

## 🚀 Quick Start

```javascript
// 1. 기업 목록 조회 후 드롭다운 생성
const companies = await getCompanies();

// 2. 두산퓨얼셀 2025년 분석 실행
const analysis = await analyzeCompany('두산퓨얼셀', { year: 2025 });

// 3. 결과 표시
displayAnalysisResult(analysis);
```

**🎯 핵심**: 모든 API는 게이트웨이(`/gateway/v1/material`)를 통해 접근하며, 비동기 처리와 에러 핸들링이 필수입니다. 