"""Users, their inventory, photo scans, matches and alerts."""

import enum
import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    REAL,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from recall_radar.db.base import Base
from recall_radar.models.recall import EMBEDDING_DIM, _enum


class ScanStatus(enum.StrEnum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class MatchStatus(enum.StrEnum):
    active = "active"
    dismissed = "dismissed"
    resolved = "resolved"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text)  # null if using external auth
    display_name: Mapped[str | None] = mapped_column(Text)
    alert_email: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Item(Base):
    """Something a user owns. Vehicles store the VIN plus the decoded make/model/year."""

    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    nickname: Mapped[str | None] = mapped_column(Text)  # "Kid's car seat"
    category: Mapped[str | None] = mapped_column(String(64))
    brand: Mapped[str | None] = mapped_column(Text)
    model_number: Mapped[str | None] = mapped_column(Text)
    model_norm: Mapped[str | None] = mapped_column(Text)
    serial_or_lot: Mapped[str | None] = mapped_column(Text)
    upc: Mapped[str | None] = mapped_column(String(14))
    vin: Mapped[str | None] = mapped_column(String(17))
    vehicle_make: Mapped[str | None] = mapped_column(String(64))
    vehicle_model: Mapped[str | None] = mapped_column(String(128))
    vehicle_year: Mapped[int | None] = mapped_column(Integer)
    purchased_on: Mapped[date | None] = mapped_column(Date)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Scan(Base):
    """A photo the user uploaded, and what the OCR/LLM pipeline read from it."""

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("items.id", ondelete="SET NULL"))
    image_key: Mapped[str] = mapped_column(Text)  # object storage key
    status: Mapped[ScanStatus] = mapped_column(
        _enum(ScanStatus, "scan_status"), server_default=ScanStatus.queued.value
    )
    ocr_text: Mapped[str | None] = mapped_column(Text)
    extracted: Mapped[dict | None] = mapped_column(JSONB)  # {brand, model, lot, upc, confidence}
    user_corrected: Mapped[dict | None] = mapped_column(JSONB)  # edits = free labeled data
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Match(Base):
    """An item that a recall applies to.

    Points at the recall (always) and the specific product (when one was matched), so vehicle
    matches, which go through recall_vehicles, fit the same table.
    """

    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("item_id", "recall_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    recall_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recalls.id", ondelete="CASCADE"), index=True
    )
    recall_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("recall_products.id", ondelete="CASCADE")
    )
    confidence: Mapped[float] = mapped_column(REAL)
    reasons: Mapped[dict] = mapped_column(JSONB)  # which signals fired, for explainability
    status: Mapped[MatchStatus] = mapped_column(
        _enum(MatchStatus, "match_status"), server_default=MatchStatus.active.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(16), server_default="email")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
