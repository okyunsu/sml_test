#!/bin/bash

echo "SASB Service starting..."

# Railway PORT 체크 - 없으면 에러
if [ -z "$PORT" ]; then
  echo "❌ ERROR: PORT environment variable not provided by Railway!"
  echo "Railway must set PORT for external access"
  exit 1
fi

echo "Using Railway PORT: $PORT"
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" 