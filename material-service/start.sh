#!/bin/bash

echo "=== Material Service Debug Start ==="
echo "1️⃣ Environment Check:"
echo "   PWD: $(pwd)"
echo "   USER: $(whoami)"
echo "   PORT: $PORT"
echo "   PYTHONPATH: $PYTHONPATH"

echo "2️⃣ Directory Structure:"
ls -la

echo "3️⃣ Shared Directory Check:"
ls -la shared/ || echo "❌ shared directory missing"

echo "4️⃣ Python Basic Test:"
python -c "print('✅ Python OK')" || echo "❌ Python Failed"

echo "5️⃣ Python Path Test:"
python -c "import sys; print('Python paths:'); [print(f'  - {p}') for p in sys.path]" || echo "❌ Python path failed"

echo "6️⃣ Import Tests (Step by Step):"
python -c "import os; print('✅ os OK')" || echo "❌ os failed"
python -c "import sys; print('✅ sys OK')" || echo "❌ sys failed"

echo "7️⃣ Shared Module Import Test:"
python -c "
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname('/app/app/main.py')))
print('✅ Path inserted:', sys.path[0])
" || echo "❌ Path insert failed"

python -c "
import sys
import os
sys.path.insert(0, '/app')
from shared.core import app_factory
print('✅ shared.core.app_factory OK')
" || echo "❌ shared module failed"

echo "8️⃣ FastAPI Import Test:"
python -c "from fastapi import FastAPI; print('✅ FastAPI OK')" || echo "❌ FastAPI failed"

echo "9️⃣ Railway PORT Check:"
if [ -z "$PORT" ]; then
  echo "❌ ERROR: PORT environment variable not provided by Railway!"
  exit 1
fi
echo "✅ Using Railway PORT: $PORT"

echo "🔟 Starting Uvicorn:"
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" 