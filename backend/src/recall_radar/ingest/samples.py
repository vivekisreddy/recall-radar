"""Load the saved API samples (research/api-exploration/data/samples) into the database.

Gives a fresh dev database real data to look at before the ingestion jobs run.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from recall_radar.ingest.upsert import UpsertResult, upsert_recalls
from recall_radar.sources import cpsc, nhtsa, openfda


def load_samples(db: Session, samples_dir: Path) -> UpsertResult:
    def read(folder: str) -> list[dict]:
        return [json.loads(p.read_text()) for p in sorted((samples_dir / folder).glob("*.json"))]

    items = (
        [cpsc.normalize(r) for r in read("cpsc")]
        + [openfda.normalize(r) for r in read("openfda")]
        + nhtsa.normalize_many(read("nhtsa"))
    )
    return upsert_recalls(db, items)
