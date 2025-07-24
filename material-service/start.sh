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

echo "💡 Shared 복사 타임스탬프 확인:"
cat /app/shared_copy_timestamp.txt || echo "❌ shared_copy_timestamp.txt not found"

echo "💡 Checking shared module import:"
python -c "
import sys
sys.path.insert(0, '/app')
from shared.core.app_factory import create_fastapi_app
print('✅ shared module OK')
" || echo "❌ shared module import failed"

echo ""
echo "🚨 === app_factory.py 실제 내용 확인 === 🚨"
echo "=== app_factory.py 파일 존재 확인 ==="
ls -la /app/shared/core/app_factory.py || echo "❌ app_factory.py not found"

echo ""
echo "=== app_factory.py 서버 URL 설정 부분 확인 ==="
python -c "
import sys
sys.path.insert(0, '/app')
try:
    with open('/app/shared/core/app_factory.py', 'r') as f:
        lines = f.readlines()
        print('Total lines:', len(lines))
        print('')
        print('All lines containing \"sasb\" or \"material\" or \"server_urls\":')
        for i, line in enumerate(lines, 1):
            if any(word in line.lower() for word in ['sasb', 'material', 'server_urls', 'railway.app']):
                print(f'  {i:2d}: {line.strip()}')
except Exception as e:
    print(f'❌ Error reading app_factory.py: {e}')
"

echo ""
echo "=== FastAPI 앱 생성 테스트 (Material 제목) ==="
python -c "
import sys
sys.path.insert(0, '/app')
try:
    from shared.core.app_factory import create_fastapi_app
    app = create_fastapi_app(title='Material Assessment Service')
    print('✅ FastAPI app created successfully')
    print('📡 Servers configured:')
    for server in app.servers:
        print(f'    - {server[\"url\"]} ({server[\"description\"]})')
except Exception as e:
    print(f'❌ FastAPI app creation failed: {e}')
    import traceback
    traceback.print_exc()
"

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