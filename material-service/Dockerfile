FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 및 공통 모듈 복사
COPY ./app ./app
COPY ./shared ./shared

# 시작 스크립트 복사
COPY start.sh ./
RUN chmod +x start.sh

# 업로드 디렉토리 생성
RUN mkdir -p uploads

# materiality 파일들 명시적 복사 확인
RUN ls -la /app/app/materiality/ || echo "Warning: materiality directory not found"

# 포트 노출
EXPOSE 8004

# 애플리케이션 실행
CMD ["./start.sh"] 