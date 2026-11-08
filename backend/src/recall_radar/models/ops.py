"""Operational tables: ingestion run logs and evaluation results."""

import uuid
from datetime import datetime

from sqlalchemy import REAL, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from recall_radar.db.base import Base
from recall_radar.models.recall import RecallSource, _enum


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[RecallSource] = mapped_column(_enum(RecallSource, "recall_source"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched: Mapped[int] = mapped_column(Integer, server_default="0")
    new_recalls: Mapped[int] = mapped_column(Integer, server_default="0")
    updated_recalls: Mapped[int] = mapped_column(Integer, server_default="0")
    errors: Mapped[int] = mapped_column(Integer, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    git_sha: Mapped[str | None] = mapped_column(String(40))
    pipeline_version: Mapped[str | None] = mapped_column(String(64))
    dataset_version: Mapped[str | None] = mapped_column(String(64))
    extraction_acc: Mapped[float | None] = mapped_column(REAL)
    match_precision: Mapped[float | None] = mapped_column(REAL)
    match_recall: Mapped[float | None] = mapped_column(REAL)
    match_f1: Mapped[float | None] = mapped_column(REAL)
    p95_latency_ms: Mapped[int | None] = mapped_column(Integer)
    cost_per_scan_usd: Mapped[float | None] = mapped_column(Numeric(8, 5))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
