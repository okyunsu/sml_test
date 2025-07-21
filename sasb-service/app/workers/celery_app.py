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
    # 🎯 조합 검색 방식 (개선된 정확도) - 시작 후 1분, 이후 10분마다 (개발용 빠른 실행)
    'run-combined-keywords-analysis': {
        'task': 'app.workers.analysis_worker.run_combined_keywords_analysis',
        'schedule': crontab(minute='1,11,21,31,41,51'),  # 10분 간격으로 실행 (1분 시작)
    },
    # 회사별 조합 검색 - 시작 후 3분, 이후 10분마다 (2분 오프셋)
    'run-company-combined-keywords-analysis': {
        'task': 'app.workers.analysis_worker.run_company_combined_keywords_analysis',
        'schedule': crontab(minute='3,13,23,33,43,53'),  # 10분 간격으로 실행 (3분 시작, 2분 오프셋)
    },
}

celery_app.conf.update(
    task_track_started=True,
) 