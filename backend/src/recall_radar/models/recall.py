"""Recall data: one row per agency announcement, plus the products and vehicles it covers.

Design notes (from the API exploration, research/api-exploration):
- `raw` keeps the agency's original payload so we can re-run extraction when prompts improve.
- Identifiers mostly live in free text, so `recall_products` is filled by an extraction step,
  not copied from agency fields (CPSC's Model field was empty in 93/93 recalls checked).
- Vehicles get their own table: one NHTSA campaign covers many make/model/year combinations.
"""

import enum
import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from recall_radar.db.base import Base

EMBEDDING_DIM = 1536


class RecallSource(enum.StrEnum):
    cpsc = "cpsc"
    fda = "fda"
    nhtsa = "nhtsa"


class Severity(enum.StrEnum):
    """One scale across agencies: FDA Class I/II/III, NHTSA park flags, CPSC hazard text."""

    critical = "critical"  # FDA Class I, NHTSA parkIt/parkOutSide, death/fire hazards
    high = "high"
    medium = "medium"  # FDA Class II
    low = "low"  # FDA Class III, label-only recalls


def _enum(cls: type[enum.Enum], name: str) -> Enum:
    return Enum(cls, name=name, values_callable=lambda e: [m.value for m in e])


class Recall(Base):
    __tablename__ = "recalls"
    __table_args__ = (UniqueConstraint("source", "source_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[RecallSource] = mapped_column(_enum(RecallSource, "recall_source"))
    source_id: Mapped[str] = mapped_column(String(64))  # agency's recall number
    # openFDA groups several recall numbers under one event; null for other sources.
    event_id: Mapped[str | None] = mapped_column(String(64), index=True)

    title: Mapped[str] = mapped_column(Text)
    hazard: Mapped[str | None] = mapped_column(Text)
    remedy: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(64))  # baby, appliance, food, vehicle...
    severity: Mapped[Severity | None] = mapped_column(_enum(Severity, "severity"))
    recall_date: Mapped[date | None] = mapped_column(Date, index=True)
    url: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)

    raw: Mapped[dict] = mapped_column(JSONB)
    # When the agency last changed it (CPSC LastPublishDate etc.): drives re-extraction.
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extraction_model: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    products: Mapped[list["RecallProduct"]] = relationship(
        back_populates="recall", cascade="all, delete-orphan"
    )
    vehicles: Mapped[list["RecallVehicle"]] = relationship(
        back_populates="recall", cascade="all, delete-orphan"
    )


class RecallProduct(Base):
    """One recalled product/model inside a recall. Filled by the extraction pipeline."""

    __tablename__ = "recall_products"
    __table_args__ = (
        Index(
            "ix_recall_products_model_norm_trgm",
            "model_norm",
            postgresql_using="gin",
            postgresql_ops={"model_norm": "gin_trgm_ops"},
        ),
        Index(
            "ix_recall_products_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recall_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recalls.id", ondelete="CASCADE"), index=True
    )
    brand: Mapped[str | None] = mapped_column(Text)
    product_name: Mapped[str | None] = mapped_column(Text)
    model_number: Mapped[str | None] = mapped_column(Text)
    model_norm: Mapped[str | None] = mapped_column(Text)  # see core/identifiers.normalize_model
    upc: Mapped[str | None] = mapped_column(String(14), index=True)
    ndc: Mapped[str | None] = mapped_column(String(16))  # drugs
    udi: Mapped[str | None] = mapped_column(String(64))  # medical devices (UDI-DI / GTIN)
    # [{"lot": "F090824LN16", "exp": "2026-08-31"}]
    lot_codes: Mapped[list | None] = mapped_column(JSONB)
    # [{"kind": "best_by", "from": "2026-08-14", "to": "2026-09-25"}]
    date_ranges: Mapped[list | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    recall: Mapped[Recall] = relationship(back_populates="products")


class RecallVehicle(Base):
    """Make/model/year covered by an NHTSA campaign. One campaign -> many rows."""

    __tablename__ = "recall_vehicles"
    __table_args__ = (
        UniqueConstraint("recall_id", "make", "model", "model_year"),
        Index("ix_recall_vehicles_lookup", "make", "model", "model_year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recall_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recalls.id", ondelete="CASCADE"))
    make: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    model_year: Mapped[int] = mapped_column(Integer)
    # e.g. "Plug-In Hybrid (4xe)" when the recall only covers a sub-type. Filled by extraction.
    applies_to: Mapped[str | None] = mapped_column(Text)

    recall: Mapped[Recall] = relationship(back_populates="vehicles")
