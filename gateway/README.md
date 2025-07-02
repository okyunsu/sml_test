# News Gateway API

News Service를 위한 API Gateway입니다.

## 🚀 실행 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Gateway API 설정
PORT=8080

# News Service URL (기본값: http://localhost:8002)
NEWS_SERVICE_URL=http://localhost:8002
```

### 3. News Service 실행
Gateway를 실행하기 전에 News Service가 8002 포트에서 실행 중인지 확인하세요.

```bash
# news-service 디렉토리에서
cd ../news-service
python -m app.main
```

### 4. Gateway 실행
```bash
python -m app.main
```

Gateway는 기본적으로 `http://localhost:8080`에서 실행됩니다.

## 📋 API 엔드포인트

### 기본 정보
- **Base URL**: `http://localhost:8080`
- **API Prefix**: `/gateway/v1`
- **Documentation**: `http://localhost:8080/docs`

### 주요 엔드포인트

#### 1. 헬스 체크
```
GET /gateway/v1/health
```

#### 2. 뉴스 검색
```
POST /gateway/v1/news/search/news
```
**요청 본문:**
```json
{
    "query": "삼성전자",
    "max_results": 100,
    "sort_by": "accuracy",
    "category": "technology",
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
}
```

#### 3. 회사 뉴스 검색
```
POST /gateway/v1/news/search/companies/{company}
```

#### 4. 회사 뉴스 분석
```
POST /gateway/v1/news/search/companies/{company}/analyze
```

#### 5. 대시보드 API
```
GET /gateway/v1/news/dashboard/status
GET /gateway/v1/news/dashboard/companies
GET /gateway/v1/news/dashboard/companies/{company}/latest
```

#### 6. 시스템 API
```
GET /gateway/v1/news/system/health
POST /gateway/v1/news/system/test/celery
```

## 🔧 설정

### 환경 변수
- `PORT`: Gateway가 실행될 포트 (기본값: 8080)
- `NEWS_SERVICE_URL`: News Service의 URL (기본값: http://localhost:8002)

### 경로 매핑
Gateway는 다음과 같이 요청을 News Service로 매핑합니다:

| Gateway 경로 | News Service 경로 |
|-------------|------------------|
| `/gateway/v1/news/search/*` | `/api/v1/search/*` |
| `/gateway/v1/news/dashboard/*` | `/api/v1/dashboard/*` |
| `/gateway/v1/news/system/*` | `/api/v1/system/*` |

## 🧪 테스트

### 1. 헬스 체크
```bash
curl http://localhost:8080/gateway/v1/health
```

### 2. 뉴스 검색 테스트
```bash
curl -X POST "http://localhost:8080/gateway/v1/news/search/news" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "삼성전자",
    "max_results": 10
  }'
```

### 3. 회사 뉴스 검색 테스트
```bash
curl -X POST "http://localhost:8080/gateway/v1/news/search/companies/삼성전자"
```

## 📝 로그

Gateway는 다음 정보를 로그로 출력합니다:
- 요청 URL과 메서드
- 요청 본문 (있는 경우)
- 응답 상태 코드
- 에러 정보 (있는 경우)

## 🔍 문제 해결

### News Service 연결 오류
1. News Service가 실행 중인지 확인
2. `NEWS_SERVICE_URL` 환경 변수 확인
3. 방화벽/네트워크 설정 확인

### JSON 파싱 오류
1. 요청 본문의 JSON 형식 확인
2. Content-Type 헤더 확인 (`application/json`)

### 경로 매핑 오류
Gateway는 자동으로 경로를 News Service API 구조에 맞게 변환합니다. 직접 News Service 경로를 사용하려면 `/gateway/v1/news/api/v1/...` 형태로 요청하세요. 