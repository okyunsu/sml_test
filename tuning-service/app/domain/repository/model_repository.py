import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ModelRepository:
    def __init__(self, db_path: str = "/app/data/models.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT UNIQUE NOT NULL,
                    model_name TEXT NOT NULL,
                    base_model TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    model_path TEXT NOT NULL,
                    file_size INTEGER,
                    hyperparameters TEXT,
                    performance_metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS training_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    model_id TEXT,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    current_epoch INTEGER,
                    total_epochs INTEGER,
                    current_step INTEGER,
                    total_steps INTEGER,
                    train_loss REAL,
                    eval_loss REAL,
                    learning_rate REAL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES models (model_id)
                )
            """)
            
            conn.commit()
    
    def save_model(self, model_data: Dict[str, Any]) -> bool:
        """모델 정보 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO models 
                    (model_id, model_name, base_model, model_type, task_type, 
                     model_path, file_size, hyperparameters, performance_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    model_data["model_id"],
                    model_data["model_name"],
                    model_data["base_model"],
                    model_data["model_type"],
                    model_data["task_type"],
                    model_data["model_path"],
                    model_data.get("file_size"),
                    json.dumps(model_data.get("hyperparameters", {})),
                    json.dumps(model_data.get("performance_metrics", {}))
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save model {model_data['model_id']}: {str(e)}")
            return False
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """모델 정보 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM models WHERE model_id = ?", (model_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    model_data = dict(row)
                    model_data["hyperparameters"] = json.loads(model_data["hyperparameters"] or "{}")
                    model_data["performance_metrics"] = json.loads(model_data["performance_metrics"] or "{}")
                    return model_data
                return None
        except Exception as e:
            logger.error(f"Failed to get model {model_id}: {str(e)}")
            return None
    
    def list_models(self) -> List[Dict[str, Any]]:
        """모델 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM models ORDER BY created_at DESC"
                )
                rows = cursor.fetchall()
                
                models = []
                for row in rows:
                    model_data = dict(row)
                    model_data["hyperparameters"] = json.loads(model_data["hyperparameters"] or "{}")
                    model_data["performance_metrics"] = json.loads(model_data["performance_metrics"] or "{}")
                    models.append(model_data)
                
                return models
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []
    
    def delete_model(self, model_id: str) -> bool:
        """모델 정보 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM models WHERE model_id = ?", (model_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete model {model_id}: {str(e)}")
            return False
    
    def save_training_job(self, job_data: Dict[str, Any]) -> bool:
        """훈련 작업 정보 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO training_jobs 
                    (job_id, model_id, status, progress, current_epoch, total_epochs,
                     current_step, total_steps, train_loss, eval_loss, learning_rate,
                     error_message, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_data["job_id"],
                    job_data.get("model_id"),
                    job_data["status"],
                    job_data.get("progress", 0.0),
                    job_data.get("current_epoch"),
                    job_data.get("total_epochs"),
                    job_data.get("current_step"),
                    job_data.get("total_steps"),
                    job_data.get("train_loss"),
                    job_data.get("eval_loss"),
                    job_data.get("learning_rate"),
                    job_data.get("error_message"),
                    job_data.get("started_at"),
                    job_data.get("completed_at")
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save training job {job_data['job_id']}: {str(e)}")
            return False
    
    def get_training_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """훈련 작업 정보 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM training_jobs WHERE job_id = ?", (job_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Failed to get training job {job_id}: {str(e)}")
            return None
    
    def list_training_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """훈련 작업 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if status:
                    cursor = conn.execute(
                        "SELECT * FROM training_jobs WHERE status = ? ORDER BY created_at DESC",
                        (status,)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM training_jobs ORDER BY created_at DESC"
                    )
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list training jobs: {str(e)}")
            return []
    
    def update_training_progress(
        self, 
        job_id: str, 
        progress: float, 
        **kwargs
    ) -> bool:
        """훈련 진행률 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 동적으로 업데이트할 필드 구성
                update_fields = ["progress = ?"]
                values = [progress]
                
                for key, value in kwargs.items():
                    if key in ["current_epoch", "total_epochs", "current_step", 
                              "total_steps", "train_loss", "eval_loss", "learning_rate"]:
                        update_fields.append(f"{key} = ?")
                        values.append(value)
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(job_id)
                
                query = f"UPDATE training_jobs SET {', '.join(update_fields)} WHERE job_id = ?"
                
                cursor = conn.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update training progress for {job_id}: {str(e)}")
            return False
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """모델 통계 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 모델 수
                cursor = conn.execute("SELECT COUNT(*) FROM models")
                total_models = cursor.fetchone()[0]
                
                # 모델 타입별 통계
                cursor = conn.execute("""
                    SELECT model_type, COUNT(*) as count 
                    FROM models 
                    GROUP BY model_type
                """)
                model_types = dict(cursor.fetchall())
                
                # 작업 타입별 통계
                cursor = conn.execute("""
                    SELECT task_type, COUNT(*) as count 
                    FROM models 
                    GROUP BY task_type
                """)
                task_types = dict(cursor.fetchall())
                
                # 총 파일 크기
                cursor = conn.execute("SELECT SUM(file_size) FROM models WHERE file_size IS NOT NULL")
                total_size = cursor.fetchone()[0] or 0
                
                return {
                    "total_models": total_models,
                    "model_types": model_types,
                    "task_types": task_types,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }
        except Exception as e:
            logger.error(f"Failed to get model statistics: {str(e)}")
            return {} 