import os
import shutil
from datetime import datetime
from typing import List, Dict, Any
import logging
from pathlib import Path

from fastapi import UploadFile
import aiofiles

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        # Docker 환경과 로컬 환경 구분
        if os.path.exists("/app"):
            # Docker 환경
            self.upload_dir = "/app/data/uploads"
            self.reports_dir = "/app/data/reports"
        else:
            # 로컬 환경
            self.upload_dir = "data/uploads"
            self.reports_dir = "data/reports"
        
        # 디렉토리 생성
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """업로드된 파일 저장"""
        try:
            # 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(self.upload_dir, filename)
            
            # 파일 저장
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {str(e)}")
            raise ValueError(f"파일 저장 중 오류가 발생했습니다: {str(e)}")
    
    async def save_multiple_files(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """여러 파일 저장"""
        saved_files = []
        
        for file in files:
            try:
                file_path = await self.save_uploaded_file(file)
                saved_files.append({
                    "original_name": file.filename,
                    "saved_path": file_path,
                    "size": file.size,
                    "content_type": file.content_type,
                    "uploaded_at": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to save file {file.filename}: {str(e)}")
                # 실패한 파일은 건너뛰고 계속 진행
                continue
        
        return saved_files
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """파일 정보 조회"""
        if not os.path.exists(file_path):
            raise ValueError(f"파일을 찾을 수 없습니다: {file_path}")
        
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    
    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """업로드된 파일 목록 조회"""
        files = []
        
        if os.path.exists(self.upload_dir):
            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        file_info = self.get_file_info(file_path)
                        files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Failed to get info for file {filename}: {str(e)}")
        
        return files
    
    def delete_file(self, file_path: str) -> bool:
        """파일 삭제"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    def move_to_reports(self, file_path: str) -> str:
        """파일을 reports 디렉토리로 이동"""
        try:
            filename = os.path.basename(file_path)
            new_path = os.path.join(self.reports_dir, filename)
            
            shutil.move(file_path, new_path)
            logger.info(f"File moved from {file_path} to {new_path}")
            return new_path
            
        except Exception as e:
            logger.error(f"Failed to move file {file_path}: {str(e)}")
            raise ValueError(f"파일 이동 중 오류가 발생했습니다: {str(e)}")
    
    def cleanup_old_files(self, days: int = 7):
        """오래된 파일 정리"""
        try:
            current_time = datetime.now()
            deleted_count = 0
            
            for directory in [self.upload_dir, self.reports_dir]:
                if os.path.exists(directory):
                    for filename in os.listdir(directory):
                        file_path = os.path.join(directory, filename)
                        if os.path.isfile(file_path):
                            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                            if (current_time - file_time).days > days:
                                os.remove(file_path)
                                deleted_count += 1
                                logger.info(f"Old file deleted: {file_path}")
            
            logger.info(f"Cleanup completed. {deleted_count} files deleted.")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return 0
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """스토리지 사용량 조회"""
        def get_dir_size(directory):
            total_size = 0
            file_count = 0
            
            if os.path.exists(directory):
                for dirpath, dirnames, filenames in os.walk(directory):
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                        except OSError:
                            pass
            
            return total_size, file_count
        
        upload_size, upload_count = get_dir_size(self.upload_dir)
        reports_size, reports_count = get_dir_size(self.reports_dir)
        
        # models 디렉토리 경로도 환경에 따라 설정
        models_dir = "/app/models" if os.path.exists("/app") else "models"
        models_size, models_count = get_dir_size(models_dir)
        
        return {
            "uploads": {
                "size_bytes": upload_size,
                "size_mb": round(upload_size / (1024 * 1024), 2),
                "file_count": upload_count
            },
            "reports": {
                "size_bytes": reports_size,
                "size_mb": round(reports_size / (1024 * 1024), 2),
                "file_count": reports_count
            },
            "models": {
                "size_bytes": models_size,
                "size_mb": round(models_size / (1024 * 1024), 2),
                "file_count": models_count
            },
            "total": {
                "size_bytes": upload_size + reports_size + models_size,
                "size_mb": round((upload_size + reports_size + models_size) / (1024 * 1024), 2),
                "file_count": upload_count + reports_count + models_count
            }
        } 