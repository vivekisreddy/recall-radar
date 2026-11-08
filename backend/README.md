# Recall Radar · backend

FastAPI API, Celery workers and the recall data pipeline, in one Python package (`src/recall_radar`).

```bash
uv sync                                    # install
uv run alembic upgrade head                # migrate
uv run recall-radar seed ../research/api-exploration/data/samples
uv run uvicorn recall_radar.api.main:app --reload
DATABASE_URL=postgresql+psycopg://recall:recall@localhost:5432/recall_radar_test uv run pytest
```

Settings come from environment variables or the repo-root `.env` (see `../.env.example`).

## How a recall flows in

1. `sources/<agency>.py` fetches raw JSON and maps it to a `NormalizedRecall`.
2. `ingest/upsert.py` writes it idempotently (keyed on `source` + `source_id`). A changed payload clears `extracted_at` so it gets re-extracted.
3. `ingest/run.py` wraps a pull in an `ingestion_runs` row (fetched / new / updated / errors).
4. Next: an LLM step fills `recall_products` (model, UPC, lots, dates) from the free text.

## Changing the schema

Edit `models/`, then `uv run alembic revision --autogenerate -m "what changed"`, read the generated file, and commit both. CI runs `alembic check` to catch models and migrations drifting apart.
