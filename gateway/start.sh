#!/bin/bash
set -e

# PORT 환경변수가 설정되지 않았으면 기본값 사용
export PORT=${PORT:-8000}

echo "Starting Gateway Service on port $PORT..."

# Uvicorn 시작
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" 