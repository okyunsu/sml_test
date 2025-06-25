# ESG Issue Service

ESG 보고서 기반 이슈 분석 및 중요성 평가 서비스

## 기능

- ESG 이슈 추출 및 분석
- 중요성 평가 (Materiality Assessment)
- PDF 보고서 분석
- ESG 이슈 분류 및 우선순위 설정

## 기술 스택

- **Framework**: FastAPI
- **Language**: Python 3.9+
- **ML/AI**: Transformers, PyTorch
- **Document Processing**: PyPDF2, pdfplumber
- **Container**: Docker

## API 엔드포인트

- `POST /issues/extract` - ESG 이슈 추출
- `POST /issues/materiality` - 중요성 평가
- `GET /issues/health` - 서비스 상태 확인

## 개발 환경 설정

### 로컬 개발

```bash
# 개발 환경 실행 (Linux/Mac)
./dev.sh

# 개발 환경 실행 (Windows)
dev.bat
```

### Docker 개발

```bash
# 개발 환경
docker-compose -f docker-compose.dev.yml up

# 프로덕션 환경
docker-compose -f docker-compose.prod.yml up
```

## 포트

- 개발: 8005
- 프로덕션: 8005

## 디렉토리 구조

```
issue-service/
├── app/
│   ├── api/                 # API 라우터
│   │   ├── domain/
│   │   │   ├── controller/      # 비즈니스 로직 컨트롤러
│   │   │   ├── model/          # 데이터 모델 및 DTO
│   │   │   ├── repository/     # 데이터 접근 계층
│   │   │   └── service/        # 비즈니스 서비스
│   │   └── report/             # 샘플 보고서
│   └── models/                 # AI 모델 파일
├── output/                 # 출력 파일
├── main.py                 # 애플리케이션 진입점
├── dev.sh                  # 개발 스크립트 (Linux/Mac)
├── dev.bat                 # 개발 스크립트 (Windows)
├── docker-compose.dev.yml  # 개발 환경 Docker 설정
├── docker-compose.prod.yml # 프로덕션 환경 Docker 설정
└── requirements.txt        # 의존성 패키지
``` 