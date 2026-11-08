"""openFDA enforcement reports (food, drug, device). Docs: https://open.fda.gov/apis/food/enforcement/

Gotchas found in research/api-exploration/notebooks/02_openfda.ipynb:
- FDA says this data must not drive public alerts: treat it as a lookup source.
- recall_number can be "N/A" before classification; one event_id groups many recall numbers.
- UPCs hide in product_description, lots/expiry in code_info.
- Dates are YYYYMMDD strings.
"""

import hashlib
from datetime import UTC, date, datetime

import httpx

from recall_radar.models import RecallSource, Severity
from recall_radar.sources.base import NormalizedRecall, http_client, shorten

URL = "https://api.fda.gov/{endpoint}/enforcement.json"
ENDPOINTS = ("food", "drug", "device")

_SEVERITY = {"Class I": Severity.critical, "Class II": Severity.medium, "Class III": Severity.low}
_CATEGORY = {"Food": "food", "Drugs": "drug", "Devices": "device"}


def fetch(
    endpoint: str,
    start: date,
    end: date,
    *,
    limit: int = 1000,
    skip: int = 0,
    api_key: str | None = None,
    client: httpx.Client | None = None,
) -> dict:
    """One page of results reported between start and end. Page with `skip` until
    skip >= meta.results.total."""
    params: dict[str, str | int] = {
        "search": f"report_date:[{start:%Y%m%d} TO {end:%Y%m%d}]",
        "limit": limit,
        "skip": skip,
    }
    if api_key:
        params["api_key"] = api_key
    with http_client(client) as c:
        resp = c.get(URL.format(endpoint=endpoint), params=params)
        if resp.status_code == 404:  # openFDA answers 404 when a search has no matches
            return {"meta": {"results": {"total": 0}}, "results": []}
        resp.raise_for_status()
        return resp.json()


def _ymd(value: str | None) -> date | None:
    return datetime.strptime(value, "%Y%m%d").date() if value else None


def normalize(rec: dict) -> NormalizedRecall:
    description = rec.get("product_description", "")
    source_id = rec.get("recall_number") or "N/A"
    if source_id == "N/A":
        # Not classified yet: build a stable key from the event and the product text.
        digest = hashlib.sha1(description.encode()).hexdigest()[:10]
        source_id = f"pending-{rec.get('event_id')}-{digest}"
    report_date = _ymd(rec.get("report_date"))
    return NormalizedRecall(
        source=RecallSource.fda,
        source_id=source_id,
        event_id=rec.get("event_id"),
        title=shorten(description) or "Untitled FDA recall",
        raw=rec,
        hazard=rec.get("reason_for_recall"),
        category=_CATEGORY.get(rec.get("product_type", "")),
        severity=_SEVERITY.get(rec.get("classification", "")),
        recall_date=_ymd(rec.get("recall_initiation_date")),
        source_updated_at=datetime.combine(report_date, datetime.min.time(), UTC)
        if report_date
        else None,
    )
