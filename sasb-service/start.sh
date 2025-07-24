#!/bin/bash
set -e

echo "🔍 DEBUG: SASB Container started, checking environment..."
echo "🔍 DEBUG: PWD=$(pwd)"
echo "🔍 DEBUG: User=$(whoami)"
echo "🔍 DEBUG: Python version=$(python --version)"

# 환경변수 확인
echo "🔍 DEBUG: PORT environment variable: $PORT"
echo "🔍 DEBUG: All environment variables:"
env | grep -E "(PORT|RAILWAY|REDIS|MODEL)" || echo "No RAILWAY/REDIS/MODEL vars found"

# PORT 환경변수 처리 (Railway 호환)
if [ -z "$PORT" ]; then
  echo "⚠️  WARNING: PORT not set by Railway, using default 8003"
  export PORT=8003
fi

echo "🚀 Starting SASB Service on port $PORT..."

# Python 경로 확인
echo "🔍 DEBUG: Python path test..."
python -c "import sys; print('Python paths:', sys.path)" || echo "❌ Python path issue"

# shared 모듈 확인
echo "🔍 DEBUG: Checking shared module..."
python -c "from shared.core.app_factory import create_fastapi_app; print('✅ shared module OK')" || echo "❌ shared module import failed"

# ML 모델 경로 확인
echo "🔍 DEBUG: Checking model path..."
ls -la /home/appuser/app/shared/models/ || echo "⚠️  Model directory not found"

echo "🔍 DEBUG: Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" 