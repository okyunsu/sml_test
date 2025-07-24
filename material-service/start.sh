#!/bin/bash
set -e

echo "=== Material Service Debug Start ==="
echo "💡 Current PATH: $PATH"
echo "💡 Checking uvicorn path:"
which uvicorn || echo "❌ uvicorn not found in PATH"

echo "💡 Checking python and pip packages:"
python -c "import uvicorn; print('✅ uvicorn import OK')" || echo "❌ uvicorn import failed"

echo "💡 Setting Python path explicitly:"
python -c "
import sys
import os
sys.path.insert(0, '/app')
print('✅ Python path set:', sys.path[0])
"

echo "💡 Checking shared module import:"
python -c "
import sys
sys.path.insert(0, '/app')
from shared.core.app_factory import create_fastapi_app
print('✅ shared module OK')
" || echo "❌ shared module import failed"

echo "💡 Checking app.main import:"
python -c "
import sys
sys.path.insert(0, '/app')
import app.main
print('✅ app.main import OK')
" || echo "❌ app.main import failed"

# Railway PORT 체크
if [ -z "$PORT" ]; then
  echo "❌ ERROR: PORT environment variable not provided by Railway!"
  exit 1  
fi

echo "🚀 Starting Material Service on port $PORT..."
echo "💡 Using debug log level for detailed output"
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level debug || echo "❗ Uvicorn crashed with error" 