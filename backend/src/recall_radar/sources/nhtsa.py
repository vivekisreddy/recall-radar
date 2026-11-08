"""NHTSA vehicle recalls. Docs: https://www.nhtsa.gov/nhtsa-datasets-and-apis

Gotchas found in research/api-exploration/notebooks/03_nhtsa.ipynb:
- ReportReceivedDate is DD/MM/YYYY (day first).
- The same campaign comes back under every vehicle it covers, so records are grouped by
  campaign number into one recall with many vehicles.
- There's no "list everything" endpoint: the full backfill (and child car seats) comes from
  the bulk file FLAT_RCL_POST_2010.zip.
"""

from datetime import date, datetime

import httpx

from recall_radar.models import RecallSource, Severity
from recall_radar.sources.base import NormalizedRecall, VehicleRef, http_client

BY_VEHICLE_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle"
BY_CAMPAIGN_URL = "https://api.nhtsa.gov/recalls/campaignNumber"


def fetch_by_vehicle(make: str, model: str, year: int, client: httpx.Client | None = None) -> list:
    params = {"make": make, "model": model, "modelYear": year}
    with http_client(client) as c:
        resp = c.get(BY_VEHICLE_URL, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])


def _component(value: str | None) -> str:
    """'STEERING:HYDRAULIC POWER ASSIST:PUMP' -> 'Steering › Hydraulic power assist › Pump'."""
    return " › ".join(
        part.strip().capitalize() for part in (value or "").split(":") if part.strip()
    )


def _dmy(value: str | None) -> date | None:
    return datetime.strptime(value, "%d/%m/%Y").date() if value else None


def normalize_many(records: list[dict]) -> list[NormalizedRecall]:
    """Group raw rows by campaign number: one recall, many vehicles."""
    by_campaign: dict[str, NormalizedRecall] = {}
    for rec in records:
        campaign = rec["NHTSACampaignNumber"]
        vehicle = VehicleRef(
            make=rec["Make"].strip().upper(),
            model=rec["Model"].strip().upper(),
            model_year=int(rec["ModelYear"]),
        )
        if campaign in by_campaign:
            existing = by_campaign[campaign]
            if vehicle not in existing.vehicles:
                existing.vehicles.append(vehicle)
            continue
        critical = rec.get("parkIt") or rec.get("parkOutSide")
        by_campaign[campaign] = NormalizedRecall(
            source=RecallSource.nhtsa,
            source_id=campaign,
            title=f"{rec.get('Manufacturer', '').strip()}: {_component(rec.get('Component'))}",
            raw=rec,
            hazard=rec.get("Consequence"),
            remedy=rec.get("Remedy"),
            category="vehicle",
            severity=Severity.critical if critical else None,
            recall_date=_dmy(rec.get("ReportReceivedDate")),
            vehicles=[vehicle],
        )
    return list(by_campaign.values())
