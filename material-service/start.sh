#!/bin/bash
set -e

echo "=== Material Service Debug Start ==="
echo "💡 Current PATH: $PATH"
echo "💡 Checking uvicorn path:"
which uvicorn || echo "❌ uvicorn not found in PATH"

echo "💡 Checking python and pip packages:"
python -c "import uvicorn; print('✅ uvicorn import OK')" || echo "❌ uvicorn import failed"

# Railway PORT 체크
if [ -z "$PORT" ]; then
  echo "❌ ERROR: PORT environment variable not provided by Railway!"
  exit 1  
fi

echo "🚀 Starting Material Service on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" 