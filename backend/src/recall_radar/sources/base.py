"""The common shape every agency payload is mapped into before it touches the database."""

from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from datetime import date, datetime

import httpx

from recall_radar.models import RecallSource, Severity

USER_AGENT = "RecallRadar/0.1 (+https://github.com/vivekisreddy/recall-radar)"


def http_client(client: httpx.Client | None = None) -> AbstractContextManager[httpx.Client]:
    """Use the caller's client (tests, connection reuse) without closing it, or make a new one."""
    if client is not None:
        return nullcontext(client)
    return httpx.Client(timeout=60, headers={"User-Agent": USER_AGENT})


@dataclass
class VehicleRef:
    make: str
    model: str
    model_year: int


@dataclass
class NormalizedRecall:
    source: RecallSource
    source_id: str
    title: str
    raw: dict
    event_id: str | None = None
    hazard: str | None = None
    remedy: str | None = None
    category: str | None = None
    severity: Severity | None = None
    recall_date: date | None = None
    source_updated_at: datetime | None = None
    url: str | None = None
    image_url: str | None = None
    vehicles: list[VehicleRef] = field(default_factory=list)


def shorten(text: str | None, limit: int = 140) -> str:
    """Cut long agency text at a word boundary for use as a title."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"
