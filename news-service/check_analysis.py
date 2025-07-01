import requests
import json

try:
    # 삼성전자 분석 결과 확인
    print("=== 삼성전자 분석 결과 ===")
    response = requests.get('http://localhost:8002/api/v1/dashboard/analysis/삼성전자')
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== LG전자 분석 결과 ===")
    response = requests.get('http://localhost:8002/api/v1/dashboard/analysis/LG전자')
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 캐시 정보 ===")
    response = requests.get('http://localhost:8002/api/v1/dashboard/cache/info')
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"에러: {e}") 