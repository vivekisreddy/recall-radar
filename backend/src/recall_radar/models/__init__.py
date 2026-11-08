"""Import every model here so Alembic's autogenerate sees the full schema."""

from recall_radar.models.ops import EvalRun, IngestionRun
from recall_radar.models.recall import (
    EMBEDDING_DIM,
    Recall,
    RecallProduct,
    RecallSource,
    RecallVehicle,
    Severity,
)
from recall_radar.models.user import Alert, Item, Match, MatchStatus, Scan, ScanStatus, User

__all__ = [
    "EMBEDDING_DIM",
    "Alert",
    "EvalRun",
    "IngestionRun",
    "Item",
    "Match",
    "MatchStatus",
    "Recall",
    "RecallProduct",
    "RecallSource",
    "RecallVehicle",
    "Scan",
    "ScanStatus",
    "Severity",
    "User",
]
