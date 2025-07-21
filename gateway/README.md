# 🌐 News Gateway API - 프론트엔드 개발자 가이드

## 📋 개요

News Gateway는 **동적 프록시 기반**의 API Gateway입니다. 모든 요청을 자동으로 News Service와 SASB Service로 전달하며, 프론트엔드에서 간단하게 사용할 수 있습니다.

## 🚀 기본 정보

- **Gateway URL**: `http://localhost:8080`
- **News Service URL**: `http://localhost:8002` (직접 호출도 가능)
- **SASB Service URL**: `http://localhost:8003` (직접 호출도 가능)
- **API 문서**: `http://localhost:8080/docs`
- **아키텍처**: 동적 프록시 패턴

## 🔄 동적 프록시 패턴

모든 API 요청은 다음 패턴을 따릅니다:

```
/gateway/v1/{service}/{path}
```

- **service**: `news` 또는 `sasb` (현재 지원하는 서비스)
- **path**: 각 서비스의 실제 API 경로

### 예시 매핑
```bash
# Gateway 요청                                   →  실제 서비스 경로
POST /gateway/v1/news/search                     →  POST /api/v1/search (News Service)
GET  /gateway/v1/news/dashboard/status           →  GET  /api/v1/dashboard/status (News Service)
POST /gateway/v1/sasb/analyze/company-sasb       →  POST /api/v1/analyze/company-sasb (SASB Service)
GET  /gateway/v1/sasb/health                     →  GET  /api/v1/health (SASB Service)
```

## 📝 API 엔드포인트 전체 목록

### 🎯 1. Gateway 관리

#### 헬스체크
```http
GET /gateway/v1/health
```
**설명**: Gateway 상태 확인  
**응답 예시**:
```json
{
  "status": "healthy",
  "service": "news-gateway",
  "version": "3.0.0-dynamic",
  "target_service": "news-service",
  "proxy_type": "dynamic"
}
```

#### 연결 테스트
```http
GET /gateway/v1/debug/connection
```
**설명**: News Service 연결 상태 테스트

---

### 🔍 2. 뉴스 검색 기능

#### 일반 뉴스 검색
```http
POST /gateway/v1/news/search
Content-Type: application/json

{
  "query": "삼성전자",
  "max_results": 10,
  "date_from": "2024-01-01",
  "date_to": "2024-12-31"
}
```

**응답 예시**:
```json
{
  "results": [
    {
      "title": "삼성전자 실적 발표",
      "content": "...",
      "url": "https://...",
      "published_at": "2024-01-15T09:00:00Z",
      "source": "연합뉴스"
    }
  ],
  "total_count": 25,
  "cache_hit": false,
  "search_time": 1.2
}
```

#### 회사별 뉴스 검색
```http
POST /gateway/v1/news/companies/{company}
```

**예시**:
```bash
POST /gateway/v1/news/companies/삼성전자
POST /gateway/v1/news/companies/LG전자
```

#### 회사 뉴스 AI 분석
```http
POST /gateway/v1/news/companies/{company}/analyze
```

**응답 예시**:
```json
{
  "company": "삼성전자",
  "analysis": {
    "sentiment": {
      "positive": 0.7,
      "negative": 0.2,
      "neutral": 0.1
    },
    "esg_score": {
      "environmental": 0.6,
      "social": 0.8,
      "governance": 0.7
    },
    "keywords": ["실적", "성장", "투자"],
    "summary": "전반적으로 긍정적인 뉴스가 많음"
  },
  "cache_hit": true,
  "analyzed_at": "2024-01-15T10:30:00Z"
}
```

---

### 📊 3. 대시보드 관리

#### 전체 시스템 상태
```http
GET /gateway/v1/news/dashboard/status
```

**응답 예시**:
```json
{
  "status": "healthy",
  "redis_connected": true,
  "celery_active": true,
  "monitored_companies": 5,
  "cache_hit_rate": 0.85,
  "last_analysis": "2024-01-15T10:00:00Z"
}
```

#### 모니터링 회사 목록
```http
GET /gateway/v1/news/dashboard/companies
```

#### 특정 회사 최신 분석
```http
GET /gateway/v1/news/dashboard/companies/{company}
```

#### 회사 분석 히스토리
```http
GET /gateway/v1/news/dashboard/companies/{company}/history?limit=20
```

#### 모든 회사 최신 분석
```http
GET /gateway/v1/news/dashboard/analysis/latest
```

#### 수동 분석 요청
```http
POST /gateway/v1/news/dashboard/companies/{company}/analyze
```

---

### 🗄️ 4. 캐시 관리

#### 캐시 정보 조회
```http
GET /gateway/v1/news/cache/info
```

**응답 예시**:
```json
{
  "companies": {
    "삼성전자": {
      "latest_exists": true,
      "history_count": 15,
      "last_updated": "2024-01-15T09:30:00Z"
    }
  },
  "cache_settings": {
    "cache_expire_hours": 24,
    "history_max_count": 100
  }
}
```

#### 특정 회사 캐시 삭제
```http
DELETE /gateway/v1/news/cache/{company}
```

---

### 🔧 5. 시스템 관리

#### 시스템 헬스체크
```http
GET /gateway/v1/news/system/health
```

#### Celery 작업자 테스트
```http
GET /gateway/v1/news/system/celery/test
GET /gateway/v1/news/system/celery/result
```

---

## 💻 프론트엔드 사용 예시

### JavaScript/TypeScript

```typescript
// 기본 설정
const GATEWAY_URL = 'http://localhost:8080';
const API_BASE = `${GATEWAY_URL}/gateway/v1/news`;

// 뉴스 검색
async function searchNews(query: string) {
  const response = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      max_results: 10,
      date_from: '2024-01-01',
      date_to: '2024-12-31'
    })
  });
  
  return await response.json();
}

// 회사 뉴스 검색
async function getCompanyNews(company: string) {
  const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(company)}`, {
    method: 'POST'
  });
  
  return await response.json();
}

// 회사 뉴스 분석
async function analyzeCompanyNews(company: string) {
  const response = await fetch(`${API_BASE}/companies/${encodeURIComponent(company)}/analyze`, {
    method: 'POST'
  });
  
  return await response.json();
}

// 대시보드 상태
async function getDashboardStatus() {
  const response = await fetch(`${API_BASE}/dashboard/status`);
  return await response.json();
}

// 캐시 정보
async function getCacheInfo() {
  const response = await fetch(`${API_BASE}/cache/info`);
  return await response.json();
}
```

### React Hook 예시

```typescript
import { useState, useEffect } from 'react';

function useNewsSearch() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const searchNews = async (query: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: 10 })
      });
      
      if (!response.ok) throw new Error('검색 실패');
      
      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { results, loading, error, searchNews };
}
```

### Python 예시

```python
import requests
import json

class NewsGatewayClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = f"{base_url}/gateway/v1/news"
    
    def search_news(self, query, max_results=10):
        """뉴스 검색"""
        response = requests.post(
            f"{self.base_url}/search",
            json={
                "query": query,
                "max_results": max_results,
                "date_from": "2024-01-01",
                "date_to": "2024-12-31"
            }
        )
        return response.json()
    
    def get_company_news(self, company):
        """회사 뉴스 검색"""
        response = requests.post(f"{self.base_url}/companies/{company}")
        return response.json()
    
    def analyze_company_news(self, company):
        """회사 뉴스 분석"""
        response = requests.post(f"{self.base_url}/companies/{company}/analyze")
        return response.json()
    
    def get_dashboard_status(self):
        """대시보드 상태"""
        response = requests.get(f"{self.base_url}/dashboard/status")
        return response.json()

# 사용 예시
client = NewsGatewayClient()
news_results = client.search_news("삼성전자")
company_analysis = client.analyze_company_news("삼성전자")
```

---

## 🔧 개발 환경 설정

### Docker Compose 실행
```bash
# 전체 서비스 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f gateway
docker-compose logs -f news-service
```

### 테스트 실행
```bash
# 모든 엔드포인트 테스트
chmod +x test-endpoints.sh
./test-endpoints.sh
```

---

## 🚨 에러 처리

### 일반적인 HTTP 상태 코드
- **200**: 성공
- **400**: 잘못된 요청 (필수 파라미터 누락 등)
- **404**: 경로 없음 또는 리소스 없음
- **500**: 서버 내부 오류

### 에러 응답 형식
```json
{
  "detail": "에러 메시지",
  "error_type": "ValidationError",
  "status_code": 400
}
```

---

## 🌟 주요 특징

### ✅ 장점
- **🚀 간단한 API 구조**: 일관된 패턴
- **🗄️ 자동 캐시**: 응답 속도 최적화
- **📊 실시간 대시보드**: 시스템 상태 모니터링
- **🔄 동적 프록시**: 새 API 자동 지원
- **🎯 타입 안전**: TypeScript 지원

### ⚡ 성능 최적화
- **캐시 우선**: 검색 30분, 분석 60분 캐시
- **백그라운드 처리**: 무거운 작업은 Celery로
- **Redis 캐시**: 빠른 응답 시간

---

## 🆘 문제 해결

### 연결 문제
```bash
# Gateway 상태 확인
curl http://localhost:8080/gateway/v1/health

# 연결 테스트
curl http://localhost:8080/gateway/v1/debug/connection
```

### 캐시 문제
```bash
# 캐시 정보 확인
curl http://localhost:8080/gateway/v1/news/cache/info

# 특정 회사 캐시 삭제  
curl -X DELETE http://localhost:8080/gateway/v1/news/cache/삼성전자
```

### 로그 확인
```bash
# Gateway 로그
docker-compose logs -f gateway

# News Service 로그
docker-compose logs -f news-service

# Redis 로그
docker-compose logs -f redis
```

---

## 📞 지원

- **API 문서**: http://localhost:8080/docs
- **Swagger UI**: 인터랙티브 API 테스트
- **Docker 상태**: `docker-compose ps`

---

## 🔮 향후 계획

- [ ] 인증/권한 시스템 추가
- [ ] Rate Limiting 구현
- [ ] 로그 수집 및 모니터링 강화
- [ ] 멀티 서비스 지원 확장 