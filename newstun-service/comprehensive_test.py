import sys 
import torch 
import platform 
import psutil 
print("="*60) 
print("RTX 2080 newstun-service 종합 환경 테스트") 
print("="*60) 
print() 
print("🖥️  시스템 정보:") 
print(f"   OS: {platform.system()} {platform.release()}") 
print(f"   CPU: {platform.processor()}") 
print(f"   RAM: {psutil.virtual_memory().total / 1024**3:.1f}GB") 
print(f"   Python: {sys.version.split()[0]}") 
print() 
print("🐍 Python 패키지 테스트:") 
try: 
    import torch 
    print(f"   ✓ PyTorch: {torch.__version__}") 
except ImportError: 
    print("   ✗ PyTorch 설치되지 않음") 
try: 
    import transformers 
    print(f"   ✓ Transformers: {transformers.__version__}") 
except ImportError: 
    print("   ✗ Transformers 설치되지 않음") 
try: 
    import fastapi 
    print(f"   ✓ FastAPI: {fastapi.__version__}") 
except ImportError: 
    print("   ✗ FastAPI 설치되지 않음") 
try: 
    import datasets 
    print(f"   ✓ Datasets: {datasets.__version__}") 
except ImportError: 
    print("   ✗ Datasets 설치되지 않음") 
try: 
    import accelerate 
    print(f"   ✓ Accelerate: {accelerate.__version__}") 
except ImportError: 
    print("   ✗ Accelerate 설치되지 않음") 
print() 
print("🎮 GPU/CUDA 환경:") 
if torch.cuda.is_available(): 
    print(f"   ✓ CUDA 사용 가능: {torch.version.cuda}") 
    device_count = torch.cuda.device_count() 
    print(f"   ✓ GPU 개수: {device_count}") 
    for i in range(device_count): 
        gpu_name = torch.cuda.get_device_name(i) 
        gpu_props = torch.cuda.get_device_properties(i) 
        total_memory = gpu_props.total_memory / 1024**3 
        print(f"   GPU {i}: {gpu_name}") 
        print(f"          메모리: {total_memory:.1f}GB") 
        if "RTX 2080" in gpu_name: 
            print("          🚀 RTX 2080 최적화 가능!") 
        torch.cuda.empty_cache() 
        test_tensor = torch.randn(100, 100).cuda(i) 
        allocated = torch.cuda.memory_allocated(i) / 1024**2 
        print(f"          테스트 할당: {allocated:.1f}MB") 
        del test_tensor 
        torch.cuda.empty_cache() 
else: 
    print("   ⚠ CUDA 사용 불가 - CPU 모드로 실행") 
print() 
print("🤖 한국어 모델 호환성 테스트:") 
recommended_models = [ 
    "klue/roberta-base", 
    "beomi/KcBERT-Base", 
    "klue/bert-base" 
] 
try: 
    from transformers import AutoTokenizer, AutoModel 
    for model_name in recommended_models: 
        try: 
            tokenizer = AutoTokenizer.from_pretrained(model_name) 
            print(f"   ✓ {model_name} 토크나이저 로드 성공") 
        except Exception as e: 
            print(f"   ⚠ {model_name} 토크나이저 로드 실패: {str(e)[:50]}...") 
except ImportError: 
    print("   ✗ Transformers가 설치되지 않아 모델 테스트 불가") 
print() 
print("📁 디렉토리 구조 확인:") 
import os 
required_dirs = ['data', 'data/training', 'models', 'output', 'logs', 'app/sample_datasets'] 
for dir_path in required_dirs: 
    if os.path.exists(dir_path): 
        print(f"   ✓ {dir_path}") 
    else: 
        print(f"   ✗ {dir_path} (누락)") 
print() 
