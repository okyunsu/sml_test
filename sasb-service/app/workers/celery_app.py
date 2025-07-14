from celery import Celery
from celery.schedules import crontab
from ..config.settings import settings

celery_app = Celery(
    "sasb_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.analysis_worker"]
)

celery_app.conf.beat_schedule = {
    # 🎯 조합 검색 방식 (개선된 정확도) - 처음 시작 후 5분, 이후 30분마다
    'run-combined-keywords-analysis': {
        'task': 'app.workers.analysis_worker.run_combined_keywords_analysis',
        'schedule': crontab(minute='5,35'),  # 매 시간 5분, 35분에 실행 (30분 간격)
    },
    # 회사별 조합 검색 - 처음 시작 후 5분, 이후 30분마다 (조금 오프셋)
    'run-company-combined-keywords-analysis': {
        'task': 'app.workers.analysis_worker.run_company_combined_keywords_analysis',
        'schedule': crontab(minute='10,40'),  # 매 시간 10분, 40분에 실행 (30분 간격, 5분 오프셋)
    },
}

celery_app.conf.update(
    task_track_started=True,
) 