#!/bin/bash
set -e

echo "🚨🚨🚨 === SASB SERVICE RAILWAY DEBUG === 🚨🚨🚨"

echo "🔍 STEP 1: Railway Environment Variables Check"
echo "ALL environment variables with RAILWAY/REDIS:"
env | grep -E "(RAILWAY|REDIS)" | sort || echo "❌ NO RAILWAY/REDIS environment variables found!"

echo ""
echo "🔍 STEP 2: Specific Redis Variables"
echo "REDIS_PRIVATE_URL: '${REDIS_PRIVATE_URL:-NOT_SET}'"
echo "REDIS_URL: '${REDIS_URL:-NOT_SET}'" 
echo "CELERY_BROKER_URL: '${CELERY_BROKER_URL:-NOT_SET}'"
echo "CELERY_RESULT_BACKEND: '${CELERY_RESULT_BACKEND:-NOT_SET}'"

echo ""
echo "🔍 STEP 3: PATH and uvicorn check"
echo "Current PATH: $PATH"
which uvicorn || echo "❌ uvicorn not found in PATH"

echo "💡 Checking python and pip packages:"
python -c "import uvicorn; print('✅ uvicorn import OK')" || echo "❌ uvicorn import failed"

echo "💡 Setting Python path explicitly:"
python -c "
import sys
import os
sys.path.insert(0, '/home/appuser/app')
print('✅ Python path set:', sys.path[0])
"

echo "💡 Checking shared module import:"
python -c "
import sys
sys.path.insert(0, '/home/appuser/app')
from shared.core.app_factory import create_fastapi_app
print('✅ shared module OK')
" || echo "❌ shared module import failed"

echo "💡 Checking app.main import:"
python -c "
import sys
sys.path.insert(0, '/home/appuser/app')
import app.main
print('✅ app.main import OK')
" || echo "❌ app.main import failed"

# Railway PORT 체크
if [ -z "$PORT" ]; then
  echo "❌ ERROR: PORT environment variable not provided by Railway!"
  exit 1
fi

echo "🚀 Starting SASB Service on port $PORT..."
echo "💡 Using debug log level for detailed output"
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level debug || echo "❗ Uvicorn crashed with error" 