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
echo "🔍 STEP 2.5: 컨테이너 내부 실제 파일 확인"
echo "=== Railway 컨테이너 내부 shared 디렉토리 상태 ==="
ls -la /home/appuser/app/shared/core/ || echo "❌ shared/core directory not found"

echo ""
echo "=== shared 복사 타임스탬프 확인 ==="
cat /home/appuser/app/shared_copy_timestamp.txt || echo "❌ shared_copy_timestamp.txt not found"

echo ""
echo "=== redis_factory.py 파일 존재 확인 ==="
ls -la /home/appuser/app/shared/core/redis_factory.py || echo "❌ redis_factory.py not found"

echo ""
echo "=== redis_factory.py 실제 내용 (Line 20-35) ==="
python -c "
import sys
sys.path.insert(0, '/home/appuser/app')
try:
    with open('/home/appuser/app/shared/core/redis_factory.py', 'r') as f:
        lines = f.readlines()
        print('Total lines:', len(lines))
        print('Lines 20-35:')
        for i in range(19, min(35, len(lines))):
            print(f'  {i+1:2d}: {lines[i].rstrip()}')
        
        # 전체 파일에서 redis 관련 라인 찾기
        print('')
        print('All redis.* lines:')
        for i, line in enumerate(lines, 1):
            if 'redis.' in line.lower() and ('client' in line or 'Redis' in line):
                print(f'  {i:2d}: {line.strip()}')
except Exception as e:
    print(f'❌ Error reading file: {e}')
"

echo ""
echo "=== Dockerfile COPY 명령어 검증 ==="
echo "현재 작업 디렉토리: $(pwd)"
echo "shared 디렉토리 내용:"
find /home/appuser/app/shared -name "*.py" | head -10 || echo "❌ shared directory scanning failed"

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

echo ""
echo "🚨 === app_factory.py 실제 내용 확인 === 🚨"
echo "=== app_factory.py 파일 존재 확인 ==="
ls -la /home/appuser/app/shared/core/app_factory.py || echo "❌ app_factory.py not found"

echo ""
echo "=== app_factory.py 서버 URL 설정 부분 확인 ==="
python -c "
import sys
sys.path.insert(0, '/home/appuser/app')
try:
    with open('/home/appuser/app/shared/core/app_factory.py', 'r') as f:
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
echo "=== FastAPI 앱 생성 테스트 (SASB 제목) ==="
python -c "
import sys
sys.path.insert(0, '/home/appuser/app')
try:
    from shared.core.app_factory import create_fastapi_app
    app = create_fastapi_app(title='SASB Analysis Service')
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

echo ""
echo "🔄 Starting Celery Worker in background..."
# Celery Worker를 백그라운드로 실행 (Railway 환경 최적화)
nohup python -m celery -A app.workers.celery_app worker --loglevel=info > /tmp/celery_worker.log 2>&1 &
WORKER_PID=$!
echo "📋 Celery Worker PID: $WORKER_PID"

# 잠시 대기 (Worker 초기화 시간)
sleep 3

echo ""
echo "🔄 Starting Celery Beat in background..."
# Celery Beat (스케줄러)를 백그라운드로 실행
nohup python -m celery -A app.workers.celery_app beat --loglevel=info > /tmp/celery_beat.log 2>&1 &
BEAT_PID=$!
echo "📋 Celery Beat PID: $BEAT_PID"

# 잠시 대기 (Beat 초기화 시간)
sleep 3

echo ""
echo "✅ Celery Worker & Beat started successfully"
echo "📄 Worker log: /tmp/celery_worker.log"
echo "📄 Beat log: /tmp/celery_beat.log"
echo "📋 Worker PID: $WORKER_PID"
echo "📋 Beat PID: $BEAT_PID"

# PID 파일 저장 (프로세스 관리용)
echo $WORKER_PID > /tmp/celery_worker.pid
echo $BEAT_PID > /tmp/celery_beat.pid

echo ""
echo "🌐 Starting FastAPI Web Server..."
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level debug || echo "❗ Uvicorn crashed with error" 