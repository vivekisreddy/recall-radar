"""Background jobs. The pipeline from the spec, in order:

    ingest_source  ->  extract_recall_fields (LLM)  ->  embed_recall  ->  rematch_inventory
    process_scan (OCR + LLM, per upload)                              ->  send_alerts

Only ingest_source is real so far; the others are named placeholders for later weeks.
"""

from datetime import UTC, datetime, timedelta

from recall_radar.db import SessionLocal
from recall_radar.ingest.run import ingest
from recall_radar.models import RecallSource
from recall_radar.workers.celery_app import celery_app


@celery_app.task
def ping() -> str:
    """Smoke test:
    celery -A recall_radar.workers.celery_app call recall_radar.workers.tasks.ping
    """
    return "pong"


@celery_app.task
def ingest_source(source: str, days: int = 7) -> dict:
    """Pull the last `days` days from one agency. Overlapping windows are safe: upserts are
    idempotent, and the overlap catches recalls the agency published late."""
    end = datetime.now(UTC).date()
    with SessionLocal() as db:
        run = ingest(db, RecallSource(source), end - timedelta(days=days), end)
        return {
            "source": source,
            "fetched": run.fetched,
            "new": run.new_recalls,
            "updated": run.updated_recalls,
            "errors": run.errors,
        }


# TODO(week 3): extract_recall_fields — LLM -> recall_products (model, UPC, lots, dates)
# TODO(week 6): process_scan — OCR + vision LLM on an uploaded photo
# TODO(week 8): embed_recall / embed_item — pgvector embeddings
# TODO(week 9): rematch_inventory — run matching for every item against new recalls
# TODO(week 9): send_alerts — email users about new matches
