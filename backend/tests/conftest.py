"""Test setup. Database tests run the real Alembic migrations against a real Postgres
(pgvector/pgvector:pg16 in CI and docker compose), so a broken migration fails the build.

Point DATABASE_URL at a database whose name ends in `_test`; every table is wiped between tests.
"""

import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url

from recall_radar.config import get_settings

BACKEND = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(scope="session")
def migrated_db():
    url = make_url(get_settings().database_url)
    if not (url.database or "").endswith("_test"):
        pytest.exit(f"Refusing to wipe '{url.database}': use a database ending in _test", 2)
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture
def db(migrated_db):
    from recall_radar.db import SessionLocal, engine

    with engine.begin() as conn:
        tables = (
            conn.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' "
                    "AND tablename <> 'alembic_version'"
                )
            )
            .scalars()
            .all()
        )
        conn.execute(text(f"TRUNCATE {', '.join(tables)} CASCADE"))
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client(db):
    from fastapi.testclient import TestClient

    from recall_radar.api.main import app

    with TestClient(app) as c:
        yield c
