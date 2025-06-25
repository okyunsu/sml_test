#!/usr/bin/env python3
"""
RTX 2080 GPU 상태 확인 및 최적화 설정 테스트
"""

import torch
import sys
import os
from app.config.gpu_config import setup_rtx2080_environment, monitor_gpu_memory, RTX2080Config

def check_cuda_installation():
    """CUDA 설치 상태 확인"""
    print("🔍 CUDA 설치 상태 확인")
    print("-" * 40)
    
    # PyTorch CUDA 지원 확인
    print(f"PyTorch 버전: {torch.__version__}")
    print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA 버전: {torch.version.cuda}")
        print(f"cuDNN 버전: {torch.backends.cudnn.version()}")
        print(f"GPU 개수: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"GPU {i}: {props.name}")
            print(f"  - 메모리: {props.total_memory / (1024**3):.1f}GB")
            print(f"  - CUDA Capability: {props.major}.{props.minor}")
    else:
        print("❌ CUDA를 사용할 수 없습니다!")
        return False
    
    return True

def check_rtx2080_optimization():
    """RTX 2080 최적화 설정 확인"""
    print("\n🎮 RTX 2080 최적화 설정 확인")
    print("-" * 40)
    
    # GPU 환경 설정
    if not setup_rtx2080_environment():
        return False
    
    # 설정 정보 출력
    config = RTX2080Config()
    print(f"최대 메모리 사용률: {config.MAX_MEMORY_FRACTION * 100}%")
    print(f"그래디언트 체크포인팅: {config.GRADIENT_CHECKPOINTING}")
    print(f"FP16 사용: {config.TRAINING_CONFIG['fp16']}")
    
    # 배치 크기 정보
    print("\n📊 권장 배치 크기:")
    for model_type, sizes in config.BATCH_SIZES.items():
        print(f"  {model_type}:")
        for task, size in sizes.items():
            print(f"    - {task}: {size}")
    
    return True

def test_gpu_memory():
    """GPU 메모리 테스트"""
    print("\n💾 GPU 메모리 테스트")
    print("-" * 40)
    
    if not torch.cuda.is_available():
        print("❌ CUDA를 사용할 수 없습니다!")
        return False
    
    # 초기 메모리 상태
    memory_info = monitor_gpu_memory()
    print("초기 메모리 상태:")
    for key, value in memory_info.items():
        print(f"  {key}: {value}")
    
    # 간단한 텐서 생성 테스트
    try:
        print("\n🧪 텐서 생성 테스트...")
        device = torch.device("cuda:0")
        
        # 작은 텐서부터 시작
        test_tensor = torch.randn(1000, 1000, device=device)
        print(f"✅ 1000x1000 텐서 생성 성공")
        
        # 메모리 상태 확인
        memory_info = monitor_gpu_memory()
        print(f"메모리 사용량: {memory_info['usage_percent']}%")
        
        # 메모리 정리
        del test_tensor
        torch.cuda.empty_cache()
        print("✅ 메모리 정리 완료")
        
    except Exception as e:
        print(f"❌ 텐서 생성 실패: {e}")
        return False
    
    return True

def check_dependencies():
    """필요한 라이브러리 확인"""
    print("\n📚 라이브러리 의존성 확인")
    print("-" * 40)
    
    required_packages = [
        'transformers',
        'datasets',
        'peft',
        'accelerate',
        'bitsandbytes',
        'fastapi',
        'uvicorn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 설치 필요")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 누락된 패키지: {', '.join(missing_packages)}")
        print("setup_local.bat을 실행하여 설치하세요.")
        return False
    
    return True

def main():
    """메인 함수"""
    print("=" * 50)
    print("ESG Fine-tuning Service GPU 환경 확인")
    print("=" * 50)
    
    # 각 단계별 확인
    checks = [
        ("CUDA 설치", check_cuda_installation),
        ("라이브러리 의존성", check_dependencies),
        ("RTX 2080 최적화", check_rtx2080_optimization),
        ("GPU 메모리", test_gpu_memory)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
                print(f"\n❌ {check_name} 확인 실패")
            else:
                print(f"\n✅ {check_name} 확인 완료")
        except Exception as e:
            print(f"\n❌ {check_name} 확인 중 오류: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 모든 확인 완료! 서비스를 실행할 수 있습니다.")
        print("run_local.bat을 실행하여 서비스를 시작하세요.")
    else:
        print("⚠️ 일부 확인 실패. 문제를 해결한 후 다시 시도하세요.")
    print("=" * 50)

if __name__ == "__main__":
    main() 