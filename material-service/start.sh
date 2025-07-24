#!/bin/bash
set -e

echo "🔍 DEBUG: Container started, checking environment..."
echo "🔍 DEBUG: PWD=$(pwd)"
echo "🔍 DEBUG: User=$(whoami)"
echo "🔍 DEBUG: Python version=$(python --version)"

# 환경변수 확인
echo "🔍 DEBUG: PORT environment variable: $PORT"
echo "🔍 DEBUG: All environment variables:"
env | grep -E "(PORT|RAILWAY|REDIS)" || echo "No RAILWAY/REDIS vars found"

# PORT 환경변수 처리 (Railway 호환)
if [ -z "$PORT" ]; then
  echo "⚠️  WARNING: PORT not set by Railway, using default 8004"
  export PORT=8004
fi

echo "🚀 Starting Material Service on port $PORT..."

# Python 경로 확인
echo "🔍 DEBUG: Python path test..."
python -c "import sys; print('Python paths:', sys.path)" || echo "❌ Python path issue"

# shared 모듈 확인
echo "🔍 DEBUG: Checking shared module..."
python -c "from shared.core.app_factory import create_fastapi_app; print('✅ shared module OK')" || echo "❌ shared module import failed"

# Redis 연결 가능한지 확인 (선택적)
echo "🔍 DEBUG: Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" 