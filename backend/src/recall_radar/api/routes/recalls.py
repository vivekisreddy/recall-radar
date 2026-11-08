import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from recall_radar.api.schemas import Page, RecallDetail, RecallSummary, SourceCount, Stats
from recall_radar.db import get_db
from recall_radar.models import Recall, RecallSource

router = APIRouter(prefix="/recalls", tags=["recalls"])


@router.get("", response_model=Page[RecallSummary])
def list_recalls(
    source: RecallSource | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[RecallSummary]:
    """Newest recalls first. Filter by agency with ?source=cpsc|fda|nhtsa."""
    query = select(Recall)
    if source:
        query = query.where(Recall.source == source)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Recall.recall_date.desc().nulls_last(), Recall.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return Page[RecallSummary](
        items=[RecallSummary.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=Stats)
def recall_stats(db: Session = Depends(get_db)) -> Stats:
    rows = db.execute(select(Recall.source, func.count()).group_by(Recall.source)).all()
    by_source = [SourceCount(source=s, recalls=n) for s, n in sorted(rows)]
    return Stats(total=sum(c.recalls for c in by_source), by_source=by_source)


@router.get("/{recall_id}", response_model=RecallDetail)
def get_recall(recall_id: uuid.UUID, db: Session = Depends(get_db)) -> RecallDetail:
    recall = db.scalars(
        select(Recall)
        .where(Recall.id == recall_id)
        .options(selectinload(Recall.products), selectinload(Recall.vehicles))
    ).one_or_none()
    if recall is None:
        raise HTTPException(status_code=404, detail="Recall not found")
    return RecallDetail.model_validate(recall)
