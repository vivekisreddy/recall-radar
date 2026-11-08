"""FastAPI entry point. Run locally with:  uv run uvicorn recall_radar.api.main:app --reload"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException  # also catches 404s for unknown routes

from recall_radar import __version__
from recall_radar.api.routes import health, recalls
from recall_radar.config import get_settings
from recall_radar.log_config import configure_logging

log = logging.getLogger(__name__)


def _error(status: int, code: str, message: str, details: object = None) -> JSONResponse:
    """Every error the API returns has the same shape: {"error": {"code", "message", ...}}."""
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Recall Radar API",
        version=__version__,
        description="Find out if anything you own has been recalled.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return _error(exc.status_code, f"http_{exc.status_code}", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error(422, "validation_error", "Invalid request", jsonable(exc.errors()))

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", extra={"path": request.url.path})
        return _error(500, "internal_error", "Something went wrong")

    app.include_router(health.router)
    app.include_router(recalls.router, prefix="/api/v1")
    return app


def jsonable(errors: list) -> list:
    """Validation errors can carry non-JSON values (tuples, exceptions in ctx); clean them up."""

    def clean(v: object) -> object:
        if isinstance(v, tuple | list):
            return [clean(x) for x in v]
        return v if isinstance(v, str | int | float | None) else str(v)

    return [{k: clean(v) for k, v in e.items() if k != "ctx"} for e in errors]


app = create_app()
