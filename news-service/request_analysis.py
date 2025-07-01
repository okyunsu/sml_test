import requests
import json
import time

try:
    print("=== 삼성전자 수동 분석 요청 ===")
    response = requests.post('http://localhost:8002/api/v1/dashboard/analyze/삼성전자')
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    task_id = result.get('task_id')
    
    print(f"\n작업 ID: {task_id}")
    print("60초 후 결과를 확인합니다...")
    time.sleep(60)
    
    print("\n=== 분석 결과 확인 ===")
    response = requests.get('http://localhost:8002/api/v1/dashboard/analysis/삼성전자')
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"에러: {e}") 