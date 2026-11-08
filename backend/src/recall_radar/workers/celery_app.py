"""Celery app + schedule. Run with:
uv run celery -A recall_radar.workers.celery_app worker --loglevel=info
uv run celery -A recall_radar.workers.celery_app beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab

from recall_radar.config import get_settings
from recall_radar.log_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

celery_app = Celery(
    "recall_radar",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["recall_radar.workers.tasks"],
)
celery_app.conf.update(
    timezone="UTC",
    task_acks_late=True,  # a task that crashes mid-run is retried, not lost
    worker_prefetch_multiplier=1,
)

# Daily pulls (UTC). CPSC publishes on weekdays; openFDA updates weekly, so daily is plenty.
celery_app.conf.beat_schedule = {
    "ingest-cpsc-daily": {
        "task": "recall_radar.workers.tasks.ingest_source",
        "schedule": crontab(hour=6, minute=0),
        "args": ("cpsc",),
    },
    "ingest-fda-daily": {
        "task": "recall_radar.workers.tasks.ingest_source",
        "schedule": crontab(hour=6, minute=15),
        "args": ("fda",),
    },
}
