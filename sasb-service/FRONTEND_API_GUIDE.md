# SASB Service API Guide for Frontend

프론트엔드 연결을 위한 SASB (Sustainability Accounting Standards Board) Analysis Service API 가이드

## 🌐 기본 설정

### Base URL
```
🚀 Railway Production: https://sasb-production.up.railway.app
Gateway를 통한 접근: https://sasb-production.up.railway.app/api/v1
Direct 접근 (Production): https://sasb-production.up.railway.app
로컬 개발용: http://localhost:8003
```

### 헤더 설정
```javascript
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

---

## 🎯 SASB Service 특징

### 🔍 조합 키워드 시스템
- **기존 문제**: `탄소중립` → 골프장, 정부기관, 박물관 등 비관련 뉴스 포함
- **개선**: `(신재생에너지 OR 발전소) AND 탄소중립` → 신재생에너지 산업 뉴스만
- **키워드 그룹**: 
  - 산업 키워드 (33개): 신재생에너지, 태양광, 풍력, 발전소, ESS, 수소 등
  - SASB 이슈 키워드 (53개): 탄소중립, 온실가스, 폐패널, SMP, 중대재해 등

### 🤖 키워드 기반 감성 분석
- **개선**: ML 모델 없이도 정확한 감성 분석
- **키워드**: ESG/SASB 특화 긍정/부정 키워드 79개 기반
- **출력**: 3-class 분류 (긍정/부정/중립) + 신뢰도 점수 (0.0-0.9)
- **로직**: 키워드 매칭 개수 기반 감성 판단

### 🔄 백그라운드 시스템
- **Celery Worker**: 자동화된 백그라운드 뉴스 수집 및 분석
- **스케줄**: 10분 간격 정기 실행
- **Redis 캐싱**: 고성능 캐시 및 결과 저장

---

## 📚 API 엔드포인트 목록

### 🎨 1. 프론트엔드 핵심 API (실시간 분석)

#### 1.1 헬스체크
```http
GET https://sasb-production.up.railway.app/api/v1/health
```
**용도**: SASB 서비스 상태 확인  
**응답 예시**:
```json
{
  "status": "healthy",
  "service": "sasb-service", 
  "version": "2.0.0",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "features": [
    "🔍 회사 + SASB 키워드 조합 분석",
    "📊 SASB 전용 키워드 분석", 
    "💾 Redis 캐시 시스템",
    "🔄 백그라운드 자동 분석",
    "🤖 키워드 기반 감성분석"
  ]
}
```

#### 1.2 회사 + SASB 키워드 조합 분석 (핵심)
```http
POST https://sasb-production.up.railway.app/api/v1/analyze/company-sasb
```
**Query Parameters**:
- `company_name`: 분석할 회사명 (필수)
- `sasb_keywords[]`: SASB 키워드 리스트 (선택사항)
- `max_results`: 수집할 최대 뉴스 개수 (기본값: 100)

**예시 요청**:
```http
POST https://sasb-production.up.railway.app/api/v1/analyze/company-sasb?company_name=두산퓨얼셀&sasb_keywords[]=탄소중립&sasb_keywords[]=온실가스&max_results=50
```

**응답 예시**:
```json
{
  "task_id": "company_sasb_20250115_103000",
  "status": "completed",
  "searched_keywords": ["두산퓨얼셀", "탄소중립", "온실가스"],
  "keyword_analysis": {
    "company_keywords": ["두산퓨얼셀", "Doosan FuelCell", "두산"],
    "sasb_keywords": ["탄소중립", "온실가스"],
    "industry_keywords": ["연료전지", "수소에너지", "발전", "전력"],
    "total_unique_keywords": 9,
    "keyword_matching_performance": {
      "high_match_articles": 28,
      "medium_match_articles": 12,
      "low_match_articles": 5,
      "average_match_score": 0.74
    }
  },
  "total_articles_found": 45,
  "company_name": "두산퓨얼셀",
  "analysis_type": "company_sasb",
  "analyzed_articles": [
    {
      "title": "두산퓨얼셀, 탄소중립 위한 수소연료전지 기술 혁신",
      "description": "두산퓨얼셀이 탄소중립 달성을 위해 수소연료전지 기술을...",
      "link": "https://news.example.com/123",
      "pub_date": "2025-01-15T10:00:00.000Z",
      "matched_keywords": ["두산퓨얼셀", "탄소중립", "수소연료전지"],
      "keyword_relevance_score": 0.85,
      "sentiment": {
        "sentiment": "긍정",
        "confidence": 0.85,
        "analysis_method": "keyword_based",
        "matched_positive_keywords": ["혁신", "발전", "성과"],
        "matched_negative_keywords": []
      },
      "sasb_classification": {
        "primary_issue": "E-GHG",
        "confidence": 0.75,
        "supporting_keywords": ["탄소중립", "온실가스", "수소에너지"]
      }
    }
  ]
}
```
**프론트엔드 활용**: 기업별 ESG 이슈 분석, 감성 분석 결과

#### 1.3 SASB 전용 키워드 분석
```http
POST https://sasb-production.up.railway.app/api/v1/analyze/sasb-only
```
**Query Parameters**:
- `sasb_keywords[]`: SASB 키워드 목록 (선택사항, 미지정시 기본값 사용)
- `max_results`: 수집할 최대 뉴스 개수 (기본값: 100)

**예시 요청**:
```http
POST https://sasb-production.up.railway.app/api/v1/analyze/sasb-only?sasb_keywords[]=탄소중립&sasb_keywords[]=재생에너지&max_results=100
```

**응답 구조**: 위와 동일하지만 `company_name`은 `null`

---

### 📊 2. 대시보드 관리 API

#### 2.1 시스템 전체 상태
```http
GET https://sasb-production.up.railway.app/api/v1/dashboard/status
```
**용도**: SASB 시스템 전체 상태 및 Redis 연결 확인  
**응답 예시**:
```json
{
  "status": "healthy",
  "redis_connected": true,
  "worker_status": "active",
  "last_analysis_time": "2025-01-15T10:25:00.000Z",
  "cache_info": {
    "total_keys": 15,
    "memory_usage": "2.3MB"
  }
}
```

#### 2.2 모니터링 회사 목록
```http
GET https://sasb-production.up.railway.app/api/v1/dashboard/companies
```
**응답 예시**:
```json
{
  "companies": ["두산퓨얼셀", "LS ELECTRIC", "한국중부발전"],
  "total_count": 3,
  "last_updated": "2025-01-15T10:30:00.000Z"
}
```

#### 2.3 SASB 뉴스 분석 결과 조회
```http
GET https://sasb-production.up.railway.app/api/v1/dashboard/sasb-news
```
**Query Parameters**:
- `max_results`: 반환할 최대 뉴스 개수 (기본값: 100)
- `force_realtime`: 실시간 분석 강제 실행 (기본값: false)
- `sasb_keywords[]`: SASB 키워드 목록 (선택사항)

**특징**: Worker 결과 우선, 캐시된 결과로 빠른 응답

---

### 🔄 3. Worker 백그라운드 시스템 API (고성능)

#### 3.1 Worker 전체 상태
```http
GET https://sasb-production.up.railway.app/api/v1/workers/status
```
**응답 예시**:
```json
{
  "status": "active",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "tasks": {
    "combined_keywords_analysis": "COMPLETED",
    "company_combined_keywords_analysis": "IN_PROGRESS"
  },
  "next_scheduled_runs": {
    "combined_keywords_analysis": "2025-01-15T10:31:00.000Z",
    "company_combined_keywords_analysis": "2025-01-15T10:33:00.000Z"
  },
  "total_active_tasks": 1
}
```

#### 3.2 🎯 조합 키워드 검색 결과 (고정확도)
```http
GET https://sasb-production.up.railway.app/api/v1/workers/results/combined-keywords
```
**Query Parameters**:
- `max_results`: 반환할 최대 뉴스 개수 (기본값: 100)

**특징**: (산업 키워드) AND (SASB 이슈 키워드) 조합으로 관련성 높은 뉴스만 수집

**응답 예시**:
```json
{
  "task_id": "combined_keywords_analysis",
  "status": "completed", 
  "searched_keywords": ["🎯 산업+이슈 조합 키워드"],
  "total_articles_found": 78,
  "analysis_type": "combined_keywords",
  "analyzed_articles": [
    {
      "title": "신재생에너지 업계, ESG 경영 강화로 탄소중립 앞당긴다",
      "description": "국내 신재생에너지 기업들이 ESG...",
      "link": "https://news.naver.com/renewable-energy-esg",
      "sentiment": {
        "sentiment": "긍정",
        "confidence": 0.82,
        "analysis_method": "keyword_based"
      }
    }
  ]
}
```
**프론트엔드 활용**: 메인 대시보드, 업계 트렌드 분석

#### 3.3 🎯 회사별 조합 검색 결과
```http
GET https://sasb-production.up.railway.app/api/v1/workers/results/company-combined/{company}
```
**Path Parameters**:
- `company`: 회사명 (예: "두산퓨얼셀", "LS ELECTRIC", "한국중부발전")

**Query Parameters**:
- `max_results`: 반환할 최대 뉴스 개수 (기본값: 100)

**예시 요청**:
```http
GET https://sasb-production.up.railway.app/api/v1/workers/results/company-combined/두산퓨얼셀?max_results=50
```

**특징**: 특정 회사 + (산업 키워드) AND (SASB 이슈 키워드) 조합

#### 3.4 Worker SASB 뉴스 결과
```http
GET https://sasb-production.up.railway.app/api/v1/workers/results/sasb-news
```
**특징**: Worker에서 백그라운드로 처리한 SASB 뉴스 분석 결과

#### 3.5 Worker 스케줄 정보
```http
GET https://sasb-production.up.railway.app/api/v1/workers/schedule
```
**응답 예시**:
```json
{
  "current_time": "2025-01-15T10:30:00.000Z",
  "scheduled_tasks": [
    {
      "name": "🎯 조합 키워드 분석",
      "schedule": "시작 후 1분, 이후 10분마다 (1,11,21,31,41,51분)",
      "next_run": "2025-01-15T10:31:00.000Z",
      "description": "(산업 키워드) AND (SASB 이슈 키워드) 조합 검색으로 정확도 높은 뉴스 수집"
    }
  ]
}
```

---

### 🗄️ 4. 캐시 관리 API

#### 4.1 캐시 정보 조회
```http
GET https://sasb-production.up.railway.app/api/v1/cache/info
```

#### 4.2 회사별 캐시 삭제
```http
DELETE https://sasb-production.up.railway.app/api/v1/cache/company/{company}
```

---

## 💻 프론트엔드 연동 예시 (JavaScript)

### 1. SASB 서비스 상태 확인
```javascript
async function checkSASBStatus() {
  try {
    const response = await fetch('https://sasb-production.up.railway.app/api/v1/health');
    const status = await response.json();
    
    return {
      isHealthy: status.status === 'healthy',
      version: status.version,
      features: status.features
    };
  } catch (error) {
    console.error('SASB 상태 확인 실패:', error);
    return { isHealthy: false, error: error.message };
  }
}
```

### 2. 기업별 SASB 분석 실행
```javascript
async function analyzeCompanySASB(companyName, options = {}) {
  const {
    sasbKeywords = ['탄소중립', '온실가스', 'ESG'],
    maxResults = 100
  } = options;
  
  const params = new URLSearchParams({
    company_name: companyName,
    max_results: maxResults.toString()
  });
  
  // 배열 파라미터 추가
  sasbKeywords.forEach(keyword => {
    params.append('sasb_keywords[]', keyword);
  });
  
  try {
    const response = await fetch(
      `https://sasb-production.up.railway.app/api/v1/analyze/company-sasb?${params}`,
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
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('SASB 분석 실패:', error);
    throw error;
  }
}
```

### 3. 고정확도 조합 키워드 결과 조회 (권장)
```javascript
async function getCombinedKeywordResults(maxResults = 100) {
  try {
    const response = await fetch(
      `https://sasb-production.up.railway.app/api/v1/workers/results/combined-keywords?max_results=${maxResults}`
    );
    
    if (!response.ok) {
      if (response.status === 404) {
        // Worker 결과가 없는 경우
        throw new Error('Worker가 아직 실행되지 않았습니다. 잠시 후 다시 시도해주세요.');
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('조합 키워드 결과 조회 실패:', error);
    throw error;
  }
}
```

### 4. Worker 상태 모니터링
```javascript
async function getWorkerStatus() {
  try {
    const response = await fetch('https://sasb-production.up.railway.app/api/v1/workers/status');
    const status = await response.json();
    
    return {
      isActive: status.status === 'active',
      activeTasks: status.total_active_tasks,
      nextRuns: status.next_scheduled_runs,
      taskStatus: status.tasks
    };
  } catch (error) {
    console.error('Worker 상태 확인 실패:', error);
    throw error;
  }
}
```

### 5. 실제 사용 예시 - SASB 대시보드 구성
```javascript
class SASBDashboard {
  constructor() {
    this.refreshInterval = null;
    this.baseUrl = 'https://sasb-production.up.railway.app';
  }
  
  async initialize() {
    // 1. 서비스 상태 확인
    const status = await checkSASBStatus();
    this.displayServiceStatus(status);
    
    // 2. 고정확도 조합 검색 결과 로드 (권장)
    await this.loadCombinedResults();
    
    // 3. Worker 상태 모니터링 시작
    this.startWorkerMonitoring();
    
    // 4. 자동 갱신 설정 (10분마다)
    this.refreshInterval = setInterval(() => {
      this.refreshData();
    }, 10 * 60 * 1000);
  }
  
  async loadCombinedResults() {
    try {
      showLoadingSpinner('뉴스 분석 결과를 불러오는 중...');
      
      const results = await getCombinedKeywordResults(50);
      this.displayNewsResults(results.analyzed_articles);
      this.displaySentimentAnalysis(results.analyzed_articles);
      
    } catch (error) {
      if (error.message.includes('Worker가 아직')) {
        showInfoMessage('백그라운드 분석이 진행중입니다. 잠시 후 결과가 표시됩니다.');
      } else {
        showErrorMessage('뉴스 분석 결과를 불러올 수 없습니다.');
      }
    } finally {
      hideLoadingSpinner();
    }
  }
  
  async analyzeSpecificCompany(companyName) {
    try {
      showLoadingSpinner(`${companyName} 분석 중...`);
      
      const result = await analyzeCompanySASB(companyName, {
        sasbKeywords: ['탄소중립', '온실가스', '재생에너지'],
        maxResults: 30
      });
      
      this.displayCompanyAnalysis(result);
      
    } catch (error) {
      showErrorMessage(`${companyName} 분석 중 오류가 발생했습니다.`);
    } finally {
      hideLoadingSpinner();
    }
  }
  
  displayNewsResults(articles) {
    const container = document.getElementById('news-results');
    
    container.innerHTML = articles.map(article => `
      <div class="news-card">
        <h3><a href="${article.link}" target="_blank">${article.title}</a></h3>
        <p>${article.description}</p>
        <div class="metadata">
          <span class="sentiment ${article.sentiment.sentiment}">
            ${article.sentiment.sentiment} (${(article.sentiment.confidence * 100).toFixed(1)}%)
          </span>
          <span class="method">키워드 기반</span>
          <span class="date">${new Date(article.pub_date).toLocaleDateString()}</span>
          <a href="${article.link}" target="_blank" class="read-more">기사 보기</a>
        </div>
        <div class="keyword-info">
          <strong>매칭 키워드:</strong> 
          ${article.matched_keywords?.map(kw => `<span class="matched-keyword">${kw}</span>`).join(' ') || 'N/A'}
          <span class="relevance-score">관련성: ${((article.keyword_relevance_score || 0) * 100).toFixed(1)}점</span>
        </div>
      </div>
    `).join('');
  }
  
  displaySentimentAnalysis(articles) {
    const sentiments = articles.reduce((acc, article) => {
      const sentiment = article.sentiment.sentiment;
      acc[sentiment] = (acc[sentiment] || 0) + 1;
      return acc;
    }, {});
    
    // 감성 분석 차트 생성
    this.createSentimentChart(sentiments);
  }

  // 🔍 키워드 분석 기능 추가
  displayKeywordAnalysis(analysisResult) {
    const keywordAnalysis = analysisResult.keyword_analysis;
    if (!keywordAnalysis) return;

    const container = document.getElementById('keyword-analysis');
    
    container.innerHTML = `
      <div class="keyword-summary">
        <h3>🔍 SASB 키워드 분석</h3>
        <div class="keyword-stats">
          <div class="stat-item">
            <span class="label">회사 키워드:</span>
            <span class="value">${keywordAnalysis.company_keywords?.length || 0}개</span>
            <div class="keywords">${keywordAnalysis.company_keywords?.join(', ') || 'N/A'}</div>
          </div>
          <div class="stat-item">
            <span class="label">SASB 키워드:</span>
            <span class="value">${keywordAnalysis.sasb_keywords?.length || 0}개</span>
            <div class="keywords">${keywordAnalysis.sasb_keywords?.join(', ') || 'N/A'}</div>
          </div>
          <div class="stat-item">
            <span class="label">산업 키워드:</span>
            <span class="value">${keywordAnalysis.industry_keywords?.length || 0}개</span>
            <div class="keywords">${keywordAnalysis.industry_keywords?.join(', ') || 'N/A'}</div>
          </div>
        </div>
      </div>
      
      <div class="matching-performance">
        <h4>📊 키워드 매칭 성과</h4>
        <div class="performance-metrics">
          <div class="metric">
            <span class="metric-label">고관련성 기사:</span>
            <span class="metric-value">${keywordAnalysis.keyword_matching_performance?.high_match_articles || 0}개</span>
          </div>
          <div class="metric">
            <span class="metric-label">중관련성 기사:</span>
            <span class="metric-value">${keywordAnalysis.keyword_matching_performance?.medium_match_articles || 0}개</span>
          </div>
          <div class="metric">
            <span class="metric-label">평균 매칭 점수:</span>
            <span class="metric-value">${((keywordAnalysis.keyword_matching_performance?.average_match_score || 0) * 100).toFixed(1)}점</span>
          </div>
        </div>
      </div>
    `;
  }

  async analyzeCompanyWithKeywordTracking(companyName) {
    try {
      showLoadingSpinner(`${companyName} SASB 키워드 분석 중...`);
      
      const result = await analyzeCompanySASB(companyName, {
        sasbKeywords: ['탄소중립', '온실가스', '재생에너지'],
        maxResults: 50
      });
      
      // 기본 분석 결과 표시
      this.displayNewsResults(result.analyzed_articles);
      this.displaySentimentAnalysis(result.analyzed_articles);
      
      // 키워드 분석 표시
      this.displayKeywordAnalysis(result);
      
      // 키워드 성과 로깅
      if (result.keyword_analysis) {
        console.log('🎯 SASB 키워드 분석 결과:', {
          totalKeywords: result.keyword_analysis.total_unique_keywords,
          avgMatchScore: result.keyword_analysis.keyword_matching_performance?.average_match_score,
          topPerformingKeywords: result.analyzed_articles
            .filter(article => article.keyword_relevance_score > 0.8)
            .flatMap(article => article.matched_keywords)
            .slice(0, 10)
        });
      }
      
    } catch (error) {
      showErrorMessage(`${companyName} SASB 키워드 분석 중 오류가 발생했습니다.`);
    } finally {
      hideLoadingSpinner();
    }
  }
}

// 사용 예시
const dashboard = new SASBDashboard();
dashboard.initialize();
```

---

## 🔧 에러 처리 및 상태 관리

### 일반적인 에러 응답
```json
{
  "detail": "오류 메시지",
  "status_code": 404
}
```

### 주요 에러 상황
1. **404**: Worker 결과 없음 - "Worker가 실행될 때까지 기다려주세요"
2. **500**: 분석 실패 - 내부 서버 오류
3. **400**: 잘못된 요청 파라미터

### 에러 처리 전략
```javascript
async function handleSASBApiCall(apiCall) {
  try {
    const result = await apiCall();
    return { success: true, data: result };
  } catch (error) {
    if (error.message.includes('Worker가 아직')) {
      return {
        success: false,
        needsRetry: true,
        message: '백그라운드 분석 진행중입니다. 잠시 후 다시 시도해주세요.'
      };
    }
    
    return {
      success: false,
      needsRetry: false,
      message: error.message
    };
  }
}
```

---

## 📊 UI 구성 권장사항

### 1. SASB 메인 대시보드
```javascript
// 권장 구성
const dashboardLayout = {
  header: {
    title: 'SASB ESG 뉴스 분석',
    statusIndicator: 'checkSASBStatus()',  // 실시간 상태
  },
  main: {
    combinedResults: 'getCombinedKeywordResults()',  // 고정확도 결과
    sentimentChart: '키워드 기반 감성 분석 차트',
    trendAnalysis: '트렌드 분석'
  },
  sidebar: {
    workerStatus: 'getWorkerStatus()',  // Worker 모니터링
    companies: '기업별 분석 버튼 (두산퓨얠셀, LS ELECTRIC, 한국중부발전)'
  }
};
```

### 2. 기업별 분석 페이지
- **기업 선택**: 두산퓨얼셀, LS ELECTRIC, 한국중부발전
- **실시간 분석**: `analyzeCompanySASB()`
- **Worker 결과**: `getCompanyWorkerResults()`

### 3. 성능 최적화 팁
- **Worker 결과 우선 사용**: 캐시된 결과로 빠른 로딩
- **실시간은 필요시만**: 사용자 요청시에만 실시간 분석 실행
- **자동 갱신**: 10분 간격으로 Worker 결과 갱신

---

## 🚀 Quick Start

```javascript
// 1. SASB 서비스 상태 확인
const status = await checkSASBStatus();

// 2. 고정확도 조합 키워드 결과 조회 (권장)
const news = await getCombinedKeywordResults(50);

// 3. 기업별 분석 (필요시)
const analysis = await analyzeCompanySASB('두산퓨얼셀');

// 4. Worker 상태 모니터링
const workerStatus = await getWorkerStatus();

// 5. 키워드 추적 분석 (NEW!)
const dashboard = new SASBDashboard();
await dashboard.analyzeCompanyWithKeywordTracking('두산퓨얼셀');

// 6. 키워드 분석 결과 확인
if (analysis.keyword_analysis) {
  console.log('🔍 키워드 분석:', {
    totalKeywords: analysis.keyword_analysis.total_unique_keywords,
    avgScore: analysis.keyword_analysis.keyword_matching_performance.average_match_score,
    companyKeywords: analysis.keyword_analysis.company_keywords,
    sasbKeywords: analysis.keyword_analysis.sasb_keywords
  });
}
```

**🎯 핵심 특징**: 
- **고정확도**: 조합 키워드 시스템으로 관련성 높은 뉴스만 수집
- **고성능**: Worker 백그라운드 처리로 빠른 응답
- **실시간**: 필요시 즉시 분석 가능
- **지능형**: 키워드 기반 ESG/SASB 특화 감성 분석 (79개 키워드)
- **확장성**: 3개 회사 지원 (두산퓨얼셀, LS ELECTRIC, 한국중부발전)
- **🔍 키워드 추적**: 매칭 키워드, 관련성 점수, 감성분석 키워드 제공 