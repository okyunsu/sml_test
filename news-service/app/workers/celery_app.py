from celery import Celery
from celery.schedules import crontab
import os

# Celery 앱 생성
celery_app = Celery(
    "news_analysis_worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["app.workers.analysis_worker"]
)

# Celery 설정
celery_app.conf.update(
    # 작업 결과 설정
    result_expires=3600,  # 1시간 후 결과 만료
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    
    # 주기적 작업 스케줄 설정
    beat_schedule={
        # 30분마다 삼성전자, LG전자 뉴스 분석
        "analyze-samsung-lg-news": {
            "task": "app.workers.analysis_worker.analyze_companies_periodic",
            "schedule": crontab(minute="*/30"),  # 30분마다 실행
            "args": (["삼성전자", "LG전자"],)
        },
    },
    beat_schedule_filename="celerybeat-schedule",
)

# 작업 라우팅 설정 (기본 celery 큐 사용)
# celery_app.conf.task_routes = {
#     "app.workers.analysis_worker.*": {"queue": "news_analysis"},
# } 