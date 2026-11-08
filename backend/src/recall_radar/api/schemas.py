"""Response shapes. Kept separate from the database models so the API contract is explicit."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from recall_radar.models import RecallSource, Severity


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RecallSummary(_Out):
    id: uuid.UUID
    source: RecallSource
    source_id: str
    title: str
    hazard: str | None
    category: str | None
    severity: Severity | None
    recall_date: date | None
    image_url: str | None


class VehicleOut(_Out):
    make: str
    model: str
    model_year: int
    applies_to: str | None


class RecallProductOut(_Out):
    brand: str | None
    product_name: str | None
    model_number: str | None
    upc: str | None
    lot_codes: list | None
    date_ranges: list | None


class RecallDetail(RecallSummary):
    event_id: str | None
    remedy: str | None
    url: str | None
    products: list[RecallProductOut]
    vehicles: list[VehicleOut]


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class SourceCount(BaseModel):
    source: RecallSource
    recalls: int


class Stats(BaseModel):
    total: int
    by_source: list[SourceCount]


class Health(BaseModel):
    status: str
    database: str
    version: str
