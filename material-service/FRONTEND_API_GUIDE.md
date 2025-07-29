# Material Service API Guide for Frontend

프론트엔드 연결을 위한 Material Assessment Service API 가이드

## 🌐 기본 설정

### Base URL
```
🚀 Railway Production: https://material-production.up.railway.app
Gateway를 통한 접근: https://material-production.up.railway.app/api/v1
Direct 접근 (Production): https://material-production.up.railway.app
로컬 개발용: http://localhost:8004
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
GET https://material-production.up.railway.app/api/v1/materiality/health
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
GET https://material-production.up.railway.app/api/v1/materiality/companies
```
**용도**: 분석 가능한 기업 목록 조회  
**응답 예시**:
```json
{
  "status": "success",
  "total_companies": 3,
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
    },
    {
      "company_name": "한국중부발전",
      "has_assessment": true,
      "available_years": [2024, 2025]
    }
  ]
}
```
**프론트엔드 활용**: 드롭다운, 기업 선택 UI

#### 1.3 특정 기업 중대성 평가 조회
```http
GET https://material-production.up.railway.app/api/v1/materiality/companies/{company_name}/assessment/{year}
```
**매개변수**:
- `company_name`: 기업명 (예: "두산퓨얼셀", "LS ELECTRIC", "한국중부발전")
- `year`: 연도 (예: 2024)

**예시 요청**:
```http
GET https://material-production.up.railway.app/api/v1/materiality/companies/두산퓨얼셀/assessment/2024
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
GET https://material-production.up.railway.app/api/v1/materiality/industries
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
      "related_companies": ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"]
    }
  ]
}
```

#### 1.5 기업별 중대성 평가 비교
```http
GET https://material-production.up.railway.app/api/v1/materiality/companies/{company_name}/compare?year1={year1}&year2={year2}
```
**매개변수**:
- `company_name`: 기업명
- `year1`: 기준 연도 (Query Parameter)
- `year2`: 비교 연도 (Query Parameter)

**예시 요청**:
```http
GET https://material-production.up.railway.app/api/v1/materiality/companies/두산퓨얼셀/compare?year1=2024&year2=2025
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
POST https://material-production.up.railway.app/api/v1/materiality/companies/{company_name}/analyze
```
**매개변수**:
- `company_name`: 기업명 (Path Parameter)
- `year`: 분석 연도 (Query Parameter, 기본값: 2025)
- `include_news`: 뉴스 분석 포함 여부 (Query Parameter, 기본값: true)
- `max_articles`: 분석할 최대 뉴스 수 (Query Parameter, 기본값: 100)

**예시 요청**:
```http
POST https://material-production.up.railway.app/api/v1/materiality/companies/두산퓨얼셀/analyze?year=2025&include_news=true&max_articles=100
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
    "search_strategy": "광범위한 키워드 매핑 + 회사별 특화 키워드",
    "search_keywords": {
      "company_keywords": ["두산퓨얼셀", "Doosan FuelCell", "두산"],
      "sasb_keywords": ["탄소중립", "온실가스", "ESG", "지속가능", "친환경", "재생에너지", "에너지효율", "안전보건", "반부패", "공급망"],
      "total_keywords_used": 13
    },
    "topic_analysis": [
      {
        "topic_name": "기후변화 대응",
        "related_keywords": ["기후변화", "탄소중립", "온실가스", "탄소배출", "넷제로", "연료전지", "수소에너지", "청정에너지"],
        "total_news_count": 45,
        "relevant_news_count": 23,
        "mention_summary": "총 23회 언급",
        "keyword_matching_stats": {
          "high_relevance_articles": 15,
          "medium_relevance_articles": 8,
          "average_relevance_score": 0.72
        }
      },
      {
        "topic_name": "순환경제",
        "related_keywords": ["순환경제", "재활용", "재사용", "폐기물", "자원순환", "지속가능", "친환경"],
        "total_news_count": 12,
        "relevant_news_count": 8,
        "mention_summary": "총 8회 언급",
        "keyword_matching_stats": {
          "high_relevance_articles": 5,
          "medium_relevance_articles": 3,
          "average_relevance_score": 0.58
        }
      }
    ],
    "key_changes": [
      {
        "topic": "기후변화 대응",
        "change_type": "increased_importance",
        "confidence": 0.8,
        "rationale": "연료전지 + 탄소중립 관련 뉴스 급증",
        "supporting_keywords": ["연료전지", "탄소중립", "수소에너지"]
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
POST https://material-production.up.railway.app/api/v1/materiality/industries/{industry}/analyze
```
**매개변수**:
- `industry`: 산업명 (Path Parameter, 예: "신재생에너지")
- `year`: 분석 연도 (Query Parameter, 기본값: 2025)
- `max_articles`: 분석할 최대 뉴스 수 (Query Parameter, 기본값: 200)
- `include_sasb_mapping`: SASB 매핑 포함 여부 (Query Parameter, 기본값: true)

**예시 요청**:
```http
POST https://material-production.up.railway.app/api/v1/materiality/industries/신재생에너지/analyze?year=2025&max_articles=200
```

**응답 예시**:
```json
{
  "analysis_metadata": {
    "industry": "신재생에너지",
    "analysis_year": 2025,
    "analysis_date": "2025-01-15T10:30:00.000Z",
    "companies_analyzed": ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"],
    "disclaimer": "산업 분석 결과는 참고용입니다."
  },
  "industry_info": {
    "description": "태양광, 풍력, 연료전지 등 신재생에너지 산업",
    "key_sasb_topics": ["기후변화 대응", "환경 영향", "에너지 효율"],
    "related_companies": ["두산퓨얠셀", "LS ELECTRIC", "한국중부발전"]
  },
  "materiality_analysis": {
    "search_keywords": {
      "industry_keywords": ["신재생에너지", "태양광", "풍력", "연료전지", "ESS", "발전", "전력", "그리드"],
      "sasb_keywords": ["기후변화", "탄소중립", "환경영향", "에너지효율", "안전", "혁신"],
      "company_specific": ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"],
      "total_keywords_used": 17
    },
    "key_issues": [
      {
        "issue_name": "기후변화 대응",
        "mention_count": 45,
        "relevance_score": 0.65,
        "trend": "increasing",
        "matched_keywords": ["기후변화", "탄소중립", "온실가스", "넷제로"],
        "top_companies_mentioned": ["두산퓨얼셀", "한국중부발전"]
      }
    ],
    "emerging_issues": [
      {
        "issue_name": "수소 경제",
        "mention_count": 12,
        "trend": "emerging",
        "impact_level": "high",
        "matched_keywords": ["수소", "수소경제", "수소에너지", "연료전지"],
        "growth_potential": "매우 높음"
      }
    ]
  },
  "trend_analysis": {
    "key_trends": [
      {
        "trend_name": "수소 에너지 확산",
        "trend_direction": "increasing", 
        "impact_level": "high",
        "companies_affected": ["두산퓨얼셀", "한국중부발전"]
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
    const response = await fetch('https://material-production.up.railway.app/api/v1/materiality/companies', {
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
      `https://material-production.up.railway.app/api/v1/materiality/companies/${encodeURIComponent(companyName)}/analyze?${params}`,
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

### 4. 3개 회사 지원 확인
```javascript
async function getSupportedCompanies() {
  try {
    const companies = await getCompanies();
    console.log('지원 회사 목록:', companies.map(c => c.company_name));
    // 예상 출력: ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"]
    
    return companies;
  } catch (error) {
    console.error('기업 목록 조회 실패:', error);
    return [];
  }
}

// 한국중부발전 분석 예시
async function analyzeKomipo() {
  try {
    showLoadingSpinner('한국중부발전 분석 중...');
    
    const result = await analyzeCompany('한국중부발전', {
      year: 2025,
      includeNews: true,
      maxArticles: 100
    });
    
    console.log('한국중부발전 분석 결과:', result);
    displayAnalysisResult(result);
    
  } catch (error) {
    showErrorMessage('한국중부발전 분석 중 오류가 발생했습니다.');
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
- **기업 선택 드롭다운**: `GET /companies` (3개 회사)
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

### 5. 한국중부발전 관련 특별 처리
```javascript
// 한국중부발전은 발전/전력 업계 특성 반영
function getCompanySpecificKeywords(companyName) {
  const keywords = {
    "두산퓨얼셀": ["연료전지", "수소", "청정에너지"],
    "LS ELECTRIC": ["전력", "자동화", "스마트그리드"],
    "한국중부발전": ["발전", "화력", "친환경전환", "탄소중립"]
  };
  
  return keywords[companyName] || [];
}

// 분석 결과에서 키워드 정보 추출 및 활용
function extractKeywordInsights(analysisResult) {
  const newsAnalysis = analysisResult.news_analysis;
  
  if (!newsAnalysis) return null;
  
  return {
    // 전체 검색 키워드 정보
    searchSummary: {
      companyKeywords: newsAnalysis.search_keywords?.company_keywords || [],
      sasbKeywords: newsAnalysis.search_keywords?.sasb_keywords || [],
      totalKeywords: newsAnalysis.search_keywords?.total_keywords_used || 0
    },
    
    // 토픽별 키워드 매칭 성과
    topicPerformance: newsAnalysis.topic_analysis?.map(topic => ({
      topicName: topic.topic_name,
      keywordCount: topic.related_keywords?.length || 0,
      matchingRate: topic.relevant_news_count / topic.total_news_count,
      topKeywords: topic.related_keywords?.slice(0, 5) || [],
      relevanceScore: topic.keyword_matching_stats?.average_relevance_score || 0
    })) || [],
    
    // 성과가 좋은 키워드 식별
    bestPerformingKeywords: newsAnalysis.key_changes?.map(change => ({
      topic: change.topic,
      keywords: change.supporting_keywords || [],
      impact: change.change_type,
      confidence: change.confidence
    })) || []
  };
}

// 키워드 성과 시각화
function displayKeywordPerformance(keywordInsights) {
  const container = document.getElementById('keyword-analysis');
  
  container.innerHTML = `
    <div class="keyword-summary">
      <h3>🔍 검색 키워드 분석</h3>
      <div class="search-stats">
        <span class="stat">회사 키워드: ${keywordInsights.searchSummary.companyKeywords.length}개</span>
        <span class="stat">SASB 키워드: ${keywordInsights.searchSummary.sasbKeywords.length}개</span>
        <span class="stat">총 키워드: ${keywordInsights.searchSummary.totalKeywords}개</span>
      </div>
    </div>
    
    <div class="topic-performance">
      <h4>📊 토픽별 키워드 매칭 성과</h4>
      ${keywordInsights.topicPerformance.map(topic => `
        <div class="topic-card">
          <h5>${topic.topicName}</h5>
          <div class="performance-metrics">
            <span class="metric">매칭률: ${(topic.matchingRate * 100).toFixed(1)}%</span>
            <span class="metric">관련성: ${(topic.relevanceScore * 100).toFixed(1)}점</span>
            <span class="metric">키워드: ${topic.keywordCount}개</span>
          </div>
          <div class="top-keywords">
            <strong>핵심 키워드:</strong> 
            ${topic.topKeywords.map(kw => `<span class="keyword-tag">${kw}</span>`).join('')}
          </div>
        </div>
      `).join('')}
    </div>
    
    <div class="best-keywords">
      <h4>🎯 성과 우수 키워드</h4>
      ${keywordInsights.bestPerformingKeywords.map(item => `
        <div class="keyword-impact">
          <strong>${item.topic}</strong> (${item.impact}): 
          ${item.keywords.map(kw => `<span class="impact-keyword">${kw}</span>`).join(', ')}
          <span class="confidence">(신뢰도: ${(item.confidence * 100).toFixed(1)}%)</span>
        </div>
      `).join('')}
    </div>
  `;
}

// 사용 예시
async function analyzeWithKeywordTracking(companyName) {
  try {
    const result = await analyzeCompany(companyName, { year: 2025 });
    
    // 기본 분석 결과 표시
    displayAnalysisResult(result);
    
    // 키워드 인사이트 추출 및 표시
    const keywordInsights = extractKeywordInsights(result);
    if (keywordInsights) {
      displayKeywordPerformance(keywordInsights);
      
      // 콘솔에 키워드 분석 로그
      console.log('🔍 키워드 분석 결과:', {
        totalKeywords: keywordInsights.searchSummary.totalKeywords,
        bestTopic: keywordInsights.topicPerformance.reduce((best, topic) => 
          topic.relevanceScore > (best?.relevanceScore || 0) ? topic : best
        ),
        topKeywords: keywordInsights.bestPerformingKeywords.flatMap(item => item.keywords)
      });
    }
    
  } catch (error) {
    console.error('키워드 추적 분석 실패:', error);
  }
}
```

---

## 🚀 Quick Start (3개 회사 지원)

```javascript
// 1. 기업 목록 조회 후 드롭다운 생성 (3개 회사)
const companies = await getCompanies();
console.log('지원 회사:', companies.length); // 3

// 2. 두산퓨얼셀 2025년 분석 실행
const doosanAnalysis = await analyzeCompany('두산퓨얼셀', { year: 2025 });

// 3. LS ELECTRIC 2025년 분석 실행  
const lsAnalysis = await analyzeCompany('LS ELECTRIC', { year: 2025 });

// 4. 한국중부발전 2025년 분석 실행 (NEW!)
const komipoAnalysis = await analyzeCompany('한국중부발전', { year: 2025 });

// 5. 결과 표시
displayAnalysisResult(doosanAnalysis);
displayAnalysisResult(lsAnalysis);
displayAnalysisResult(komipoAnalysis);

// 6. 키워드 추적 분석 (NEW!)
await analyzeWithKeywordTracking('두산퓨얼셀');

// 7. 키워드 인사이트 확인
const keywordInsights = extractKeywordInsights(doosanAnalysis);
console.log('🔍 검색 키워드:', keywordInsights?.searchSummary);
console.log('📊 토픽별 성과:', keywordInsights?.topicPerformance);
```

**🎯 핵심**: 
- **3개 회사 지원**: 두산퓨얼셀, LS ELECTRIC, 한국중부발전
- **광범위한 키워드 매핑**: 실제 뉴스와 높은 매칭률
- **Railway Production**: https://material-production.up.railway.app
- **실시간 분석**: SASB Service와 연동한 종합 분석
- **비동기 처리**: 모든 API는 비동기 처리와 에러 핸들링 필수
- **🔍 키워드 추적**: 검색 키워드, 매칭 성과, 관련성 점수 제공 