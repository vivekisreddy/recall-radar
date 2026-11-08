"""Pick 20 deliberate samples per source from the raw pulls and save one JSON file per record.

Raw pulls (data/raw/) were fetched on 2026-10-20 from:
  - CPSC:    saferproducts.gov/RestWebServices/Recall  (3 date windows)
  - openFDA: api.fda.gov/{food,drug,device}/enforcement.json
  - NHTSA:   api.nhtsa.gov/recalls/recallsByVehicle + /recalls/campaignNumber
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "samples"


def save(source, key, record):
    d = OUT / source
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{key}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))


# ---------- CPSC: chosen to match the 5 use cases ----------
CPSC_PICKS = {
    # baby & kids (use case 1/2/3)
    "27027": "baby", "27018": "baby", "27029": "bedrail", "27005": "bedrail",
    "26789": "kids", "27022": "kids", "27003": "kids", "27028": "kids",
    # fire & hazard sweep (use case 4)
    "27024": "fire", "27009": "fire", "27011": "fire", "26792": "fire",
    "26798": "fire", "26791": "fire", "26793": "fire", "27007": "fire",
    # tip-over / household
    "27020": "tipover", "27010": "household",
    # older recalls that DO have ProductUPCs (2019)
    "19154": "has_upc", "19131": "has_upc",
}
cpsc = json.loads((RAW / "cpsc_window.json").read_text()) + json.loads(
    (RAW / "cpsc_older_windows.json").read_text()
)
by_num = {r["RecallNumber"]: r for r in cpsc}
for num, tag in CPSC_PICKS.items():
    rec = dict(by_num[num])
    rec["_sample_tag"] = tag
    save("cpsc", num, rec)

# ---------- openFDA: 10 food, 5 drug, 5 device (distinct events where possible) ----------
bulk = json.loads((RAW / "fda_nhtsa_bulk.json").read_text())


def fda(ep):
    return next(v["results"] for k, v in bulk.items() if f"/{ep}/enforcement" in k)


def distinct(rows, n):
    seen, out = set(), []
    for r in rows:  # first pass: one per event
        if r["event_id"] not in seen:
            seen.add(r["event_id"]); out.append(r)
    for r in rows:  # top up if needed
        if len(out) >= n: break
        if r not in out: out.append(r)
    return out[:n]


for ep, n in [("food", 10), ("drug", 5), ("device", 5)]:
    for r in distinct(fda(ep), n):
        key = r["recall_number"] if r["recall_number"] != "N/A" else f"event-{r['event_id']}"
        save("openfda", f"{ep}_{key}", {**r, "_endpoint": ep})

# ---------- NHTSA: spread across vehicles, include park-it / OTA flags ----------
nhtsa_rows = []
for k, v in bulk.items():
    if "api.nhtsa.gov" in k:
        nhtsa_rows += v["results"]
flagged = [r for r in nhtsa_rows if r["parkIt"] or r["parkOutSide"] or r["overTheAirUpdate"]]
picked, seen = [], set()
for r in flagged + nhtsa_rows:
    key = (r["NHTSACampaignNumber"], r["Make"], r["Model"])
    per_vehicle = sum(1 for p in picked if (p["Make"], p["Model"]) == (r["Make"], r["Model"]))
    if key in seen or per_vehicle >= 5:
        continue
    seen.add(key); picked.append(r)
    if len(picked) == 20:
        break
for r in picked:
    save("nhtsa", f"{r['NHTSACampaignNumber']}_{r['Make']}_{r['Model']}".replace(" ", "-").replace("/", "-"), r)

for s in ("cpsc", "openfda", "nhtsa"):
    print(s, len(list((OUT / s).glob("*.json"))), "samples")
