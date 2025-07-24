#!/bin/bash
set -e

# Railway에서 PORT 환경변수가 자동 설정됨. 없으면 종료
if [ -z "$PORT" ]; then
  echo "❌ Error: PORT environment variable is not set."
  exit 1
fi

echo "🚀 Starting SASB Service on port $PORT..."

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" 