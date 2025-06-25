from app.domain.service.gri_data_service import GRIDataService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GRIController:
    """GRI 관련 요청을 처리하는 컨트롤러"""
    
    def __init__(self):
        self.gri_service = GRIDataService()
    
    async def create_gri_standards_learning_dataset(self) -> Dict[str, Any]:
        """GRI 기준 학습 데이터셋 생성 요청 처리"""
        try:
            logger.info("🎯 GRI 기준 학습 데이터셋 생성 요청 처리")
            result = await self.gri_service.create_gri_standards_learning_dataset()
            return result
        except Exception as e:
            logger.error(f"❌ GRI 기준 학습 데이터셋 생성 실패: {str(e)}")
            raise
    
    async def create_gri_standards_dataset(self) -> Dict[str, Any]:
        """기존 GRI 표준 데이터셋 생성 (호환성 유지)"""
        try:
            logger.info("🎯 GRI 표준 데이터셋 생성 요청 처리")
            result = await self.gri_service.create_gri_standards_learning_dataset()
            return result
        except Exception as e:
            logger.error(f"❌ GRI 표준 데이터셋 생성 실패: {str(e)}")
            raise
    
    async def list_gri_models(self) -> Dict[str, Any]:
        """GRI 학습 모델 목록 조회 요청 처리"""
        try:
            logger.info("📁 GRI 모델 목록 조회 요청 처리")
            result = await self.gri_service.list_gri_models()
            return result
        except Exception as e:
            logger.error(f"❌ GRI 모델 목록 조회 실패: {str(e)}")
            raise 