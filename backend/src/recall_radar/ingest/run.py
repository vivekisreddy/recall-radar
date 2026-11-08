"""Pull a date window from one agency, upsert it, and log the run to ingestion_runs."""

import logging
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from recall_radar.config import get_settings
from recall_radar.ingest.upsert import upsert_recalls
from recall_radar.models import IngestionRun, RecallSource
from recall_radar.sources import cpsc, openfda
from recall_radar.sources.base import NormalizedRecall

log = logging.getLogger(__name__)


def _fetch(source: RecallSource, start: date, end: date) -> tuple[int, list[NormalizedRecall]]:
    if source is RecallSource.cpsc:
        raw = cpsc.fetch(start, end)
        return len(raw), [cpsc.normalize(r) for r in raw]

    if source is RecallSource.fda:
        api_key = get_settings().openfda_api_key
        rows: list[dict] = []
        for endpoint in openfda.ENDPOINTS:
            skip = 0
            while True:
                page = openfda.fetch(endpoint, start, end, skip=skip, api_key=api_key)
                rows += page["results"]
                skip += len(page["results"])
                if not page["results"] or skip >= page["meta"]["results"]["total"]:
                    break
        return len(rows), [openfda.normalize(r) for r in rows]

    # NHTSA has no date-window endpoint. TODO(week 3): ingest the FLAT_RCL bulk file.
    raise NotImplementedError("NHTSA ingestion uses the bulk file; see docs/decisions.md")


def ingest(db: Session, source: RecallSource, start: date, end: date) -> IngestionRun:
    run = IngestionRun(source=source)
    db.add(run)
    db.commit()
    try:
        fetched, items = _fetch(source, start, end)
        result = upsert_recalls(db, items)
        run.fetched = fetched
        run.new_recalls = result.new
        run.updated_recalls = result.updated
    except Exception as exc:
        db.rollback()
        run.errors = 1
        run.notes = f"{type(exc).__name__}: {exc}"[:2000]
        log.exception("ingest failed", extra={"source": source.value})
    run.finished_at = datetime.now(UTC)
    db.commit()
    log.info(
        "ingest finished",
        extra={
            "source": source.value,
            "fetched": run.fetched,
            "new": run.new_recalls,
            "updated": run.updated_recalls,
            "errors": run.errors,
        },
    )
    return run
