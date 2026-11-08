# Recall Radar · API exploration (Planning phase, week 1)

Goal: understand the three federal recall APIs well enough to design the schema,
the ingestion workers and the LLM extraction step. Samples were pulled on **2026-10-20**.

## What's here
```
recall_explore.py          shared helpers: live fetch, sample loader, regex ID finder, normaliser, coverage table
notebooks/
  01_cpsc.ipynb            CPSC (consumer products)       → identifiers hide in prose
  02_openfda.ipynb         openFDA food / drug / device   → UPCs in description, lots in code_info
  03_nhtsa.ipynb           NHTSA vehicles                 → clean schema, but model ≠ your car
  04_findings.ipynb        field map + decisions (start here if short on time)
data/samples/{cpsc,openfda,nhtsa}/   20 saved payloads per source (one JSON per recall)
data/raw/                  the full raw pulls the samples were chosen from
scripts/                   select_samples.py · build_notebooks.py · run_notebooks.py
```

## Run it
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter lab notebooks/
```
Every notebook has `LIVE = False` at the top. Set it to `True` to hit the real APIs instead of the saved samples.

## Endpoints
| Source | Endpoint | Auth | Notes |
|---|---|---|---|
| CPSC | `https://www.saferproducts.gov/RestWebServices/Recall?format=json` | none | filter by `RecallDateStart/End`, `ProductName`…; no paging |
| openFDA | `https://api.fda.gov/{food,drug,device}/enforcement.json` | optional key | `search`, `sort`, `limit` (≤1000), `skip`; weekly |
| NHTSA | `https://api.nhtsa.gov/recalls/recallsByVehicle?make=&model=&modelYear=` · `/recalls/campaignNumber` | none | daily; bulk zip `FLAT_RCL_POST_2010.zip` for backfill + car seats |

## Headline findings
1. **CPSC's `Products[].Model` field was empty in all 93 recalls checked** (2019, 2024, 2026); only 2 had `ProductUPCs`. Identifiers live in `Description` prose.
2. **openFDA packs identifiers into two free-text fields**: UPC in `product_description` (8/10 food samples), lots/expiry in `code_info` as multi-item lists.
3. **NHTSA is clean but coarse**: make/model/year match over-includes trims (e.g. plug-in-hybrid-only recalls). Dates are **DD/MM/YYYY**.
4. **openFDA is not meant for public alerts** (FDA disclaimer) → lookup + link, not push.
5. 1 in 5 CPSC samples has **no identifier at all** → semantic + photo matching needed.
