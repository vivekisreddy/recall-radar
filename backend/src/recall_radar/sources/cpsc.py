"""CPSC (consumer products). Docs: https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information

Gotchas found in research/api-exploration/notebooks/01_cpsc.ipynb:
- Products[].Model and ProductUPCs are almost always empty; identifiers are in `Description`.
- No paging: a date window returns everything in it, so ingest in small windows.
"""

from datetime import UTC, date, datetime

import httpx

from recall_radar.models import RecallSource, Severity
from recall_radar.sources.base import NormalizedRecall, http_client

URL = "https://www.saferproducts.gov/RestWebServices/Recall"


def fetch(start: date, end: date, client: httpx.Client | None = None) -> list[dict]:
    params = {
        "format": "json",
        "RecallDateStart": start.isoformat(),
        "RecallDateEnd": end.isoformat(),
    }
    with http_client(client) as c:
        resp = c.get(URL, params=params)
        resp.raise_for_status()
        return resp.json()


def _names(items: list[dict] | None) -> str | None:
    text = "; ".join(i.get("Name", "").strip() for i in items or [] if i.get("Name"))
    return text or None


def _severity(hazard: str | None) -> Severity | None:
    # First-pass heuristic. The extraction step will replace this with a proper classifier.
    h = (hazard or "").lower()
    if any(word in h for word in ("death", "fire", "suffocat", "strangulat", "entrapment")):
        return Severity.critical
    return None


def normalize(rec: dict) -> NormalizedRecall:
    hazard = _names(rec.get("Hazards"))
    images = rec.get("Images") or []
    published = rec.get("LastPublishDate")
    recall_date = rec.get("RecallDate")
    return NormalizedRecall(
        source=RecallSource.cpsc,
        source_id=str(rec["RecallNumber"]),
        title=rec.get("Title") or "Untitled CPSC recall",
        raw=rec,
        hazard=hazard,
        remedy=_names(rec.get("Remedies")),
        severity=_severity(hazard),
        recall_date=date.fromisoformat(recall_date[:10]) if recall_date else None,
        source_updated_at=datetime.fromisoformat(published).replace(tzinfo=UTC)
        if published
        else None,
        url=rec.get("URL"),
        image_url=images[0].get("URL") if images else None,
    )
