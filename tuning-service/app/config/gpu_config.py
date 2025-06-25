"""
RTX 2080 최적화 GPU 설정
- VRAM: 8GB
- CUDA Cores: 2,944
- CUDA Capability: 7.5
"""

import torch
import gc
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RTX2080Config:
    """RTX 2080 최적화 설정"""
    
    # RTX 2080 스펙
    GPU_NAME = "RTX 2080"
    VRAM_SIZE = 8  # GB
    CUDA_CAPABILITY = 7.5
    CUDA_CORES = 2944
    
    # 메모리 최적화 설정
    MAX_MEMORY_FRACTION = 0.85  # VRAM의 85%만 사용
    MEMORY_GROWTH = True
    GRADIENT_CHECKPOINTING = True
    
    # 배치 크기 최적화 (VRAM 8GB 기준)
    BATCH_SIZES = {
        "bert-base": {
            "train": 8,
            "eval": 16,
            "inference": 32
        },
        "bert-large": {
            "train": 4,
            "eval": 8,
            "inference": 16
        },
        "gpt2": {
            "train": 6,
            "eval": 12,
            "inference": 24
        }
    }
    
    # LoRA 최적화 설정
    LORA_CONFIG = {
        "r": 16,  # RTX 2080에 최적화된 rank
        "lora_alpha": 32,
        "lora_dropout": 0.1,
        "target_modules": ["query", "value", "key", "dense"]
    }
    
    # 학습 최적화 설정
    TRAINING_CONFIG = {
        "fp16": True,  # RTX 2080은 FP16 지원
        "dataloader_num_workers": 2,  # CPU 코어 수 고려
        "gradient_accumulation_steps": 4,
        "warmup_steps": 100,
        "save_steps": 500,
        "eval_steps": 250,
        "logging_steps": 50
    }

def setup_rtx2080_environment():
    """RTX 2080 환경 설정"""
    
    # CUDA 사용 가능 여부 확인
    if not torch.cuda.is_available():
        logger.error("❌ CUDA를 사용할 수 없습니다!")
        return False
    
    # GPU 정보 확인
    gpu_count = torch.cuda.device_count()
    current_device = torch.cuda.current_device()
    gpu_name = torch.cuda.get_device_name(current_device)
    
    logger.info(f"🎮 GPU 정보:")
    logger.info(f"   - 사용 가능한 GPU: {gpu_count}개")
    logger.info(f"   - 현재 GPU: {gpu_name}")
    logger.info(f"   - 디바이스 ID: {current_device}")
    
    # VRAM 정보
    total_memory = torch.cuda.get_device_properties(current_device).total_memory
    total_memory_gb = total_memory / (1024**3)
    logger.info(f"   - 총 VRAM: {total_memory_gb:.1f}GB")
    
    # RTX 2080 확인
    if "2080" in gpu_name:
        logger.info("✅ RTX 2080 감지됨 - 최적화 설정 적용")
    else:
        logger.warning(f"⚠️ RTX 2080이 아닌 GPU 감지: {gpu_name}")
    
    # 메모리 최적화 설정
    torch.cuda.empty_cache()
    gc.collect()
    
    # CUDA 메모리 할당 전략 설정
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    return True

def get_optimal_batch_size(model_type: str, task: str = "train") -> int:
    """모델 타입과 작업에 따른 최적 배치 크기 반환"""
    
    config = RTX2080Config()
    
    # 모델 타입 정규화
    if "bert" in model_type.lower():
        if "large" in model_type.lower():
            model_key = "bert-large"
        else:
            model_key = "bert-base"
    elif "gpt" in model_type.lower():
        model_key = "gpt2"
    else:
        model_key = "bert-base"  # 기본값
    
    batch_size = config.BATCH_SIZES.get(model_key, {}).get(task, 8)
    logger.info(f"🎯 최적 배치 크기: {batch_size} (모델: {model_type}, 작업: {task})")
    
    return batch_size

def monitor_gpu_memory():
    """GPU 메모리 사용량 모니터링"""
    
    if not torch.cuda.is_available():
        return {}
    
    device = torch.cuda.current_device()
    allocated = torch.cuda.memory_allocated(device)
    cached = torch.cuda.memory_reserved(device)
    total = torch.cuda.get_device_properties(device).total_memory
    
    allocated_gb = allocated / (1024**3)
    cached_gb = cached / (1024**3)
    total_gb = total / (1024**3)
    
    usage_percent = (allocated / total) * 100
    
    memory_info = {
        "allocated_gb": round(allocated_gb, 2),
        "cached_gb": round(cached_gb, 2),
        "total_gb": round(total_gb, 2),
        "usage_percent": round(usage_percent, 1),
        "free_gb": round(total_gb - allocated_gb, 2)
    }
    
    # 메모리 사용량이 80% 이상이면 경고
    if usage_percent > 80:
        logger.warning(f"⚠️ GPU 메모리 사용량 높음: {usage_percent:.1f}%")
    
    return memory_info

def cleanup_gpu_memory():
    """GPU 메모리 정리"""
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()
        logger.info("🧹 GPU 메모리 정리 완료")

def get_rtx2080_training_args() -> Dict[str, Any]:
    """RTX 2080 최적화 학습 인자 반환"""
    
    config = RTX2080Config()
    
    return {
        "per_device_train_batch_size": config.BATCH_SIZES["bert-base"]["train"],
        "per_device_eval_batch_size": config.BATCH_SIZES["bert-base"]["eval"],
        "gradient_accumulation_steps": config.TRAINING_CONFIG["gradient_accumulation_steps"],
        "warmup_steps": config.TRAINING_CONFIG["warmup_steps"],
        "save_steps": config.TRAINING_CONFIG["save_steps"],
        "eval_steps": config.TRAINING_CONFIG["eval_steps"],
        "logging_steps": config.TRAINING_CONFIG["logging_steps"],
        "fp16": config.TRAINING_CONFIG["fp16"],
        "dataloader_num_workers": config.TRAINING_CONFIG["dataloader_num_workers"],
        "gradient_checkpointing": config.GRADIENT_CHECKPOINTING,
        "remove_unused_columns": False,
        "load_best_model_at_end": True,
        "metric_for_best_model": "eval_loss",
        "greater_is_better": False,
        "save_total_limit": 2,  # 디스크 공간 절약
    }

def get_rtx2080_lora_config() -> Dict[str, Any]:
    """RTX 2080 최적화 LoRA 설정 반환"""
    
    config = RTX2080Config()
    return config.LORA_CONFIG.copy()

# 초기화 시 환경 설정
if __name__ == "__main__":
    setup_rtx2080_environment()
    memory_info = monitor_gpu_memory()
    print(f"GPU 메모리 정보: {memory_info}") 