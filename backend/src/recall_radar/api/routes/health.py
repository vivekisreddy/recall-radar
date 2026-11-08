from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from recall_radar import __version__
from recall_radar.api.schemas import Health
from recall_radar.db import get_db

router = APIRouter(tags=["ops"])


@router.get("/healthz", response_model=Health)
def healthz(response: Response, db: Session = Depends(get_db)) -> Health:
    """Liveness + database check. Load balancers and uptime monitors hit this."""
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unreachable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Health(
        status="ok" if database == "ok" else "degraded", database=database, version=__version__
    )
