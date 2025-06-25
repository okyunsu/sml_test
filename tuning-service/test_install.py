#!/usr/bin/env python3
"""
esg-tuning 환경 설치 테스트 스크립트
"""

def test_imports():
    """필수 패키지 import 테스트"""
    
    print("=" * 50)
    print("ESG Fine-tuning Service 패키지 테스트")
    print("=" * 50)
    
    packages = [
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('datasets', 'Datasets'),
        ('peft', 'PEFT'),
        ('accelerate', 'Accelerate'),
        ('bitsandbytes', 'BitsAndBytes'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('sklearn', 'Scikit-learn')
    ]
    
    success_count = 0
    
    for package, name in packages:
        try:
            __import__(package)
            print(f"✅ {name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name} - {e}")
    
    print(f"\n📊 결과: {success_count}/{len(packages)} 패키지 설치됨")
    
    return success_count == len(packages)

def test_gpu():
    """GPU 테스트"""
    
    print("\n" + "=" * 50)
    print("GPU 환경 테스트")
    print("=" * 50)
    
    try:
        import torch
        
        print(f"PyTorch 버전: {torch.__version__}")
        print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA 버전: {torch.version.cuda}")
            print(f"GPU 개수: {torch.cuda.device_count()}")
            print(f"현재 GPU: {torch.cuda.get_device_name(0)}")
            
            # 간단한 GPU 테스트
            device = torch.device("cuda:0")
            test_tensor = torch.randn(100, 100, device=device)
            result = torch.mm(test_tensor, test_tensor.t())
            print(f"✅ GPU 연산 테스트 성공 (결과 크기: {result.shape})")
            
            # 메모리 정보
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            cached = torch.cuda.memory_reserved(0) / (1024**3)
            print(f"GPU 메모리 사용량: {allocated:.2f}GB (캐시: {cached:.2f}GB)")
            
            return True
        else:
            print("❌ CUDA를 사용할 수 없습니다")
            return False
            
    except Exception as e:
        print(f"❌ GPU 테스트 실패: {e}")
        return False

def test_service():
    """서비스 구성 요소 테스트"""
    
    print("\n" + "=" * 50)
    print("서비스 구성 요소 테스트")
    print("=" * 50)
    
    try:
        # FastAPI 앱 import 테스트
        from main import app
        print("✅ FastAPI 앱 로드 성공")
        
        # GPU 설정 테스트
        from app.config.gpu_config import RTX2080Config, setup_rtx2080_environment
        print("✅ GPU 설정 모듈 로드 성공")
        
        # 환경 설정 테스트
        if setup_rtx2080_environment():
            print("✅ RTX 2080 환경 설정 성공")
        else:
            print("⚠️ RTX 2080 환경 설정 실패")
        
        return True
        
    except Exception as e:
        print(f"❌ 서비스 구성 요소 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    
    print("🚀 esg-tuning 환경 종합 테스트 시작\n")
    
    # 각 테스트 실행
    tests = [
        ("패키지 설치", test_imports),
        ("GPU 환경", test_gpu),
        ("서비스 구성", test_service)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 오류: {e}")
            results.append((test_name, False))
    
    # 최종 결과
    print("\n" + "=" * 50)
    print("최종 테스트 결과")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 전체 결과: {passed}/{len(results)} 테스트 통과")
    
    if passed == len(results):
        print("\n🎉 모든 테스트 통과! 서비스를 시작할 수 있습니다.")
        print("run_local.bat을 실행하여 서비스를 시작하세요.")
    else:
        print("\n⚠️ 일부 테스트 실패. 문제를 해결한 후 다시 시도하세요.")

if __name__ == "__main__":
    main() 