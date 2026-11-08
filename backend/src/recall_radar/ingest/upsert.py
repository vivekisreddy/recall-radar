"""Idempotent writes: running the same ingest twice never duplicates a recall."""

from dataclasses import dataclass, fields

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from recall_radar.models import Recall, RecallVehicle
from recall_radar.sources.base import NormalizedRecall

# NormalizedRecall fields copied straight onto the Recall row.
_COLUMNS = [f.name for f in fields(NormalizedRecall) if f.name not in ("vehicles",)]


@dataclass
class UpsertResult:
    new: int = 0
    updated: int = 0
    unchanged: int = 0


def upsert_recalls(db: Session, items: list[NormalizedRecall]) -> UpsertResult:
    result = UpsertResult()
    for item in items:
        existing = db.scalars(
            select(Recall)
            .where(Recall.source == item.source, Recall.source_id == item.source_id)
            .options(selectinload(Recall.vehicles))
        ).one_or_none()

        if existing is None:
            recall = Recall(**{name: getattr(item, name) for name in _COLUMNS})
            recall.vehicles = [RecallVehicle(**vars(v)) for v in item.vehicles]
            db.add(recall)
            result.new += 1
            continue

        changed = False
        for name in _COLUMNS:
            if getattr(existing, name) != getattr(item, name):
                setattr(existing, name, getattr(item, name))
                changed = True
        known = {(v.make, v.model, v.model_year) for v in existing.vehicles}
        for v in item.vehicles:
            if (v.make, v.model, v.model_year) not in known:
                existing.vehicles.append(RecallVehicle(**vars(v)))
                changed = True
        if changed:
            # Payload changed: clear the extraction stamp so the pipeline re-extracts it.
            existing.extracted_at = None
            result.updated += 1
        else:
            result.unchanged += 1
    db.commit()
    return result
