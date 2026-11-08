"""Shared helpers for the Recall Radar API-exploration notebooks.

Three jobs:
  1. fetch()        – call each agency API live (used when you re-run on your own machine)
  2. load_samples() – read the 20 saved sample payloads per source
  3. find_ids()     – regex "first pass" at pulling model / UPC / lot / serial out of prose

The regexes are deliberately simple. Their hit rate is a BASELINE: whatever they
miss is exactly the gap the LLM extraction step in week 3 has to close.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "data" / "samples"

# ---------------------------------------------------------------- live endpoints
ENDPOINTS = {
    "cpsc": "https://www.saferproducts.gov/RestWebServices/Recall",
    "openfda": "https://api.fda.gov/{endpoint}/enforcement.json",
    "nhtsa_vehicle": "https://api.nhtsa.gov/recalls/recallsByVehicle",
    "nhtsa_campaign": "https://api.nhtsa.gov/recalls/campaignNumber",
}


def fetch(source: str, timeout: int = 30, **params):
    """Live call. Examples:
    fetch("cpsc", RecallDateStart="2026-09-01", RecallDateEnd="2026-10-20")
    fetch("openfda", endpoint="food", sort="report_date:desc", limit=10)
    fetch("nhtsa_vehicle", make="honda", model="cr-v", modelYear=2018)
    """
    import requests  # imported here so offline use needs no network libs

    url = ENDPOINTS[source]
    if source == "cpsc":
        params.setdefault("format", "json")
    if source == "openfda":
        url = url.format(endpoint=params.pop("endpoint", "food"))
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def load_samples(source: str) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((SAMPLES / source).glob("*.json"))]


# ---------------------------------------------------------------- identifier regexes
# Model numbers: an anchor word, then a token containing at least one digit.
MODEL_RE = re.compile(
    r"(?:model|item|style|sku|part|catalog)\s*(?:no\.?|number|numbers|#|/catalog numbers?)?\s*[:\"“]?\s*"
    r"([A-Z0-9][A-Z0-9\-./]{1,24}[A-Z0-9])",
    re.IGNORECASE,
)
# UPC-A (12) / EAN-13 / GTIN-14, allowing the spaced print format "0 75465 11111 0"
UPC_RE = re.compile(r"(?:UPC|GTIN|barcode)[^0-9]{0,15}((?:\d[\s-]?){11,13}\d)", re.IGNORECASE)
LOT_RE = re.compile(r"(?:lot|batch)(?:\s*(?:#|no\.?|number|numbers|code|s))*\s*[:#]?\s*([A-Z0-9][A-Z0-9\-@/]{2,})", re.IGNORECASE)
SERIAL_RE = re.compile(r"serial(?:\s*(?:#|no\.?|numbers?))?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-]{3,})", re.IGNORECASE)
DATECODE_RE = re.compile(
    r"(?:best\s*(?:if\s*used\s*)?by|exp(?:iration|iry)?\.?(?:\s*date)?|bud|use\s*by|date\s*of\s*manufacture[r]?|manufactured)"
    r"[^0-9A-Za-z]{0,6}([0-9]{1,4}[/\-.][0-9]{1,2}(?:[/\-.][0-9]{2,4})?|[A-Z][a-z]+\.?\s*\d{4})",
    re.IGNORECASE,
)
NDC_RE = re.compile(r"NDC\s*:?\s*(\d{4,5}-\d{3,4}-\d{1,2})", re.IGNORECASE)
UDI_RE = re.compile(r"UDI(?:-DI)?(?:/GTIN)?\s*:?\s*(\d{14})", re.IGNORECASE)

# Words the model regex grabs by mistake ("model number is located on ...")
_MODEL_STOP = {"IS", "AND", "ON", "OF", "THE", "NUMBER", "NUMBERS", "LOCATED", "PRINTED", "CAN", "ARE"}


def normalize_model(s: str) -> str:
    """'XJ-200 b' -> 'XJ200B'  (what goes in recall_products.model_norm)."""
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def normalize_upc(s: str) -> str:
    return re.sub(r"\D", "", s)


def find_ids(text: str | None) -> dict[str, list[str]]:
    text = text or ""
    models = [m for m in MODEL_RE.findall(text) if any(c.isdigit() for c in m) and m.upper() not in _MODEL_STOP]
    return {
        "models": sorted({m.rstrip(".,;") for m in models}),
        "upcs": sorted({normalize_upc(u) for u in UPC_RE.findall(text)}),
        "lots": sorted({l.rstrip(".,;") for l in LOT_RE.findall(text) if any(c.isdigit() for c in l)}),
        "serials": sorted({s for s in SERIAL_RE.findall(text) if any(c.isdigit() for c in s)}),
        "date_codes": sorted(set(DATECODE_RE.findall(text))),
        "ndcs": sorted(set(NDC_RE.findall(text))),
        "udis": sorted(set(UDI_RE.findall(text))),
    }


# ---------------------------------------------------------------- coverage
def is_filled(v) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() not in ("", "N/A", "no codes")
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def coverage(records: list[dict], fields: list[str]):
    """% of records where each field is non-empty."""
    import pandas as pd

    rows = [{"field": f, "filled": sum(is_filled(r.get(f)) for r in records)} for f in fields]
    df = pd.DataFrame(rows)
    df["of"] = len(records)
    df["pct"] = (100 * df["filled"] / len(records)).round(0).astype(int)
    return df.set_index("field")
