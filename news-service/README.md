# News Service

뉴스 검색 및 분석을 위한 마이크로서비스입니다. 네이버 뉴스 API를 활용하여 뉴스 데이터를 수집하고, ML 서비스와 연동하여 뉴스 분석을 수행합니다.

## 주요 기능

### 1. 뉴스 검색
- **네이버 뉴스 API 연동**: 실시간 뉴스 검색
- **중복 제거**: 유사한 뉴스 자동 제거
- **유사도 필터링**: 설정 가능한 유사도 임계값
- **비동기 처리**: 고성능 비동기 검색

### 2. 회사별 뉴스 검색
- **간소화된 검색**: 회사명만 입력하면 최적화된 설정으로 검색
- **고급 검색**: 상세 옵션과 함께 검색 (검색 결과 수, 정렬 방식, 유사도 임계값 등)
- **정확도 최적화**: 회사명을 따옴표로 감싸서 정확한 검색

### 3. 뉴스 분석
- **ESG 분류**: Environmental, Social, Governance 카테고리 분류
- **감정 분석**: 긍정/부정/중립 감정 분석
- **키워드 추출**: 주요 키워드 자동 추출
- **ML 서비스 연동**: 외부 ML 서비스와 연동하여 고도화된 분석

### 4. 배치 처리
- **동시 검색**: 최대 10개의 검색 요청을 동시에 처리
- **부분 실패 허용**: 일부 요청이 실패해도 나머지 결과 반환

## API 엔드포인트

### 간소화된 엔드포인트 (추천)

#### 1. 간소화된 회사 뉴스 검색
```http
POST /api/v1/news/company/simple
Content-Type: application/json

{
    "company": "삼성전자"
}
```

**특징:**
- 회사명만 입력하면 최적화된 설정으로 검색
- 검색 결과: 100개, 정확도 순 정렬
- 중복 제거 활성화, 유사도 임계값: 0.75

#### 2. 간소화된 회사 뉴스 분석
```http
POST /api/v1/news/company/simple/analyze
Content-Type: application/json

{
    "company": "삼성전자"
}
```

**특징:**
- 뉴스 검색 + ESG 분석을 한 번에 수행
- ML 서비스와 연동하여 자동 분석

### 고급 엔드포인트

#### 1. 일반 뉴스 검색
```http
POST /api/v1/news/search
Content-Type: application/json

{
    "query": "ESG",
    "display": 10,
    "start": 1,
    "sort": "date",
    "remove_duplicates": true,
    "similarity_threshold": 0.8
}
```

#### 2. 회사별 뉴스 검색 (고급)
```http
POST /api/v1/news/company
Content-Type: application/json

{
    "company": "삼성전자",
    "display": 50,
    "start": 1,
    "sort": "date",
    "remove_duplicates": true,
    "similarity_threshold": 0.75
}
```

#### 3. 회사별 뉴스 분석 (고급)
```http
POST /api/v1/news/analyze-company
Content-Type: application/json

{
    "company": "삼성전자",
    "display": 100,
    "sort": "date"
}
```

#### 4. 배치 뉴스 검색
```http
POST /api/v1/news/search/batch
Content-Type: application/json

[
    {
        "query": "삼성전자",
        "display": 10
    },
    {
        "query": "LG전자",
        "display": 10
    }
]
```

#### 5. 트렌딩 키워드 조회
```http
GET /api/v1/news/trending
```

#### 6. 헬스체크
```http
GET /api/v1/news/health
```

## 응답 형식

### 뉴스 검색 응답
```json
{
    "last_build_date": "Mon, 25 Dec 2023 10:30:00 +0900",
    "total": 500,
    "start": 1,
    "display": 10,
    "items": [
        {
            "title": "ESG 경영 확산으로 지속가능한 성장 기대",
            "original_link": "https://example.com/news/123",
            "link": "https://news.naver.com/main/read.nhn",
            "description": "ESG 경영이 기업의 지속가능한 성장을 위한 핵심 전략으로 부상하고 있다...",
            "pub_date": "Mon, 25 Dec 2023 09:00:00 +0900",
            "mention_count": 3,
            "similarity_score": 0.95
        }
    ],
    "original_count": 15,
    "duplicates_removed": 5,
    "deduplication_enabled": true
}
```

### 뉴스 분석 응답
```json
{
    "search_info": {
        "company": "삼성전자",
        "total_searched": 100,
        "analyzed_count": 50
    },
    "analyzed_news": [
        {
            "news_item": {
                "title": "삼성전자, ESG 경영 강화",
                "description": "...",
                "link": "...",
                "pub_date": "..."
            },
            "esg_classification": {
                "esg_category": "Environmental",
                "confidence_score": 0.85,
                "keywords": ["환경", "친환경", "탄소중립"],
                "classification_method": "keyword_based"
            },
            "sentiment_analysis": {
                "sentiment": "긍정",
                "confidence_score": 0.92,
                "positive": 0.92,
                "negative": 0.05,
                "neutral": 0.03,
                "analysis_method": "ml_model"
            }
        }
    ],
    "analysis_summary": {
        "total_analyzed": 50,
        "esg_distribution": {
            "Environmental": 20,
            "Social": 15,
            "Governance": 15
        },
        "sentiment_distribution": {
            "긍정": 30,
            "중립": 15,
            "부정": 5
        }
    },
    "ml_service_status": "connected"
}
```

## 기술 스택

- **Python 3.12**
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **httpx**: 비동기 HTTP 클라이언트
- **Pydantic**: 데이터 검증 및 설정 관리
- **네이버 검색 API**: 뉴스 데이터 소스

## 주요 특징

### 1. 비동기 최적화
- 모든 API 호출이 비동기로 처리
- 배치 처리 시 동시성 활용
- 연결 풀 최적화로 성능 향상

### 2. 지능형 중복 제거
- 제목과 내용의 유사도 계산
- 설정 가능한 유사도 임계값
- 대표 뉴스 선택 및 언급 횟수 표시

### 3. 에러 처리
- 상세한 에러 메시지 제공
- HTTP 상태 코드 매핑
- 부분 실패 허용 (배치 처리)

### 4. 로깅 및 모니터링
- 구조화된 로깅
- 백그라운드 작업을 통한 비동기 로깅
- 헬스체크 엔드포인트

## 설정

### 환경 변수
```bash
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
NAVER_SEARCH_URL=https://openapi.naver.com/v1/search/news.json
ML_SERVICE_URL=http://ml-service:8000
```

### Docker 실행
```bash
# 개발 환경
docker-compose up -d

# 프로덕션 환경
docker-compose -f docker-compose.prod.yml up -d
```

## 개발 가이드

### 로컬 개발 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 성능 최적화

### 1. 연결 풀 설정
- 최대 연결 수: 100
- Keep-alive 연결 수: 20
- Keep-alive 만료 시간: 30초

### 2. 타임아웃 설정
- 연결 타임아웃: 10초
- 읽기 타임아웃: 30초
- 쓰기 타임아웃: 10초

### 3. 배치 처리
- 중복 제거를 위한 배치 크기: 50
- ESG 필터링 배치 크기: 20
- 최대 동시 요청 수: 10

## 모니터링

### 헬스체크
```http
GET /api/v1/news/health
```

### 로그 레벨
- INFO: 일반적인 요청/응답 로그
- ERROR: 에러 발생 시 상세 로그
- DEBUG: 개발 시 디버깅 정보

## 라이선스

MIT License 