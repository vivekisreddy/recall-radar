"""API + database tests. Need a real Postgres (see conftest.py)."""

from conftest import load_fixture

from recall_radar.ingest.upsert import upsert_recalls
from recall_radar.sources import cpsc, nhtsa, openfda


def seed(db):
    items = [
        cpsc.normalize(load_fixture("cpsc_27024.json")),
        openfda.normalize(load_fixture("fda_H-0016-2027.json")),
        *nhtsa.normalize_many(load_fixture("nhtsa_23V787000_two_years.json")),
    ]
    return upsert_recalls(db, items)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["database"] == "ok"


def test_upsert_is_idempotent(db):
    first = seed(db)
    second = seed(db)
    assert (first.new, first.updated) == (3, 0)
    assert (second.new, second.updated, second.unchanged) == (0, 0, 3)


def test_upsert_detects_changes(db):
    seed(db)
    changed = cpsc.normalize(load_fixture("cpsc_27024.json"))
    changed.title = "Updated title"
    result = upsert_recalls(db, [changed])
    assert result.updated == 1


def test_list_recalls(client, db):
    seed(db)
    body = client.get("/api/v1/recalls").json()
    assert body["total"] == 3
    # Newest first: CPSC 2026-10-15, FDA 2026-09-14, NHTSA 2023-11-22
    assert [r["source"] for r in body["items"]] == ["cpsc", "fda", "nhtsa"]


def test_list_recalls_filtered(client, db):
    seed(db)
    body = client.get("/api/v1/recalls", params={"source": "nhtsa"}).json()
    assert body["total"] == 1
    assert body["items"][0]["source_id"] == "23V787000"


def test_stats(client, db):
    seed(db)
    body = client.get("/api/v1/recalls/stats").json()
    assert body["total"] == 3
    assert {s["source"]: s["recalls"] for s in body["by_source"]} == {
        "cpsc": 1,
        "fda": 1,
        "nhtsa": 1,
    }


def test_recall_detail_includes_vehicles(client, db):
    seed(db)
    recall_id = client.get("/api/v1/recalls", params={"source": "nhtsa"}).json()["items"][0]["id"]
    body = client.get(f"/api/v1/recalls/{recall_id}").json()
    assert [v["model_year"] for v in body["vehicles"]] == [2021, 2022]


def test_errors_have_one_shape(client, db):
    missing = client.get("/api/v1/recalls/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "http_404"

    invalid = client.get("/api/v1/recalls", params={"limit": 0})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"
