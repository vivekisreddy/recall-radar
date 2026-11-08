"""The agency mappers, tested on real payloads saved during the API exploration."""

from datetime import UTC, date, datetime

from conftest import load_fixture

from recall_radar.models import RecallSource, Severity
from recall_radar.sources import cpsc, nhtsa, openfda
from recall_radar.sources.base import VehicleRef


def test_cpsc_normalize():
    r = cpsc.normalize(load_fixture("cpsc_27024.json"))
    assert r.source is RecallSource.cpsc
    assert r.source_id == "27024"
    assert "Thermal Laminators" in r.title
    assert r.recall_date == date(2026, 10, 15)
    assert r.source_updated_at.tzinfo is UTC  # aware, so re-ingest compares equal
    assert r.severity is Severity.critical  # fire hazard
    assert r.image_url.startswith("https://www.cpsc.gov/")


def test_openfda_normalize():
    r = openfda.normalize(load_fixture("fda_H-0016-2027.json"))
    assert r.source is RecallSource.fda
    assert r.source_id == "H-0016-2027"
    assert r.event_id == "99872"
    assert r.severity is Severity.critical  # Class I
    assert r.category == "food"
    assert r.recall_date == date(2026, 9, 14)  # from YYYYMMDD
    assert r.source_updated_at == datetime(2026, 10, 14, tzinfo=UTC)
    assert len(r.title) <= 141


def test_openfda_unclassified_recall_gets_stable_id():
    rec = load_fixture("fda_H-0016-2027.json") | {"recall_number": "N/A"}
    first, second = openfda.normalize(rec), openfda.normalize(rec)
    assert first.source_id.startswith("pending-99872-")
    assert first.source_id == second.source_id


def test_nhtsa_groups_one_campaign_into_one_recall():
    recalls = nhtsa.normalize_many(load_fixture("nhtsa_23V787000_two_years.json"))
    assert len(recalls) == 1
    r = recalls[0]
    assert r.source_id == "23V787000"
    assert r.recall_date == date(2023, 11, 22)  # parsed day-first: "22/11/2023"
    assert r.severity is Severity.critical  # parkOutSide
    assert r.vehicles == [
        VehicleRef("JEEP", "WRANGLER", 2021),
        VehicleRef("JEEP", "WRANGLER", 2022),
    ]


def test_nhtsa_title_is_readable():
    r = nhtsa.normalize_many(load_fixture("nhtsa_23V787000_two_years.json"))[0]
    assert (
        r.title
        == "Chrysler (FCA US, LLC): Electrical system › Propulsion system › Traction battery"
    )
