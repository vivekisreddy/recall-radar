"""Generates notebooks/01..04 with nbformat. Re-run after editing, then execute with:
    python scripts/build_notebooks.py && python scripts/run_notebooks.py
"""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"
NB.mkdir(exist_ok=True)

SETUP = """import sys, json, re
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))   # so we can import recall_explore from the repo root
import pandas as pd
from recall_explore import fetch, load_samples, find_ids, coverage, normalize_model
pd.set_option("display.max_colwidth", 80)

LIVE = False   # True = call the real API (needs internet). False = use the 20 saved samples."""


def nb(cells):
    n = nbf.v4.new_notebook()
    n.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    n.cells = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    return n


# =====================================================================  01 CPSC
cpsc = nb([
("md", """# 01 · CPSC Recalls API

**Agency:** U.S. Consumer Product Safety Commission — household products, toys, baby gear, furniture, electronics.
**Endpoint:** `https://www.saferproducts.gov/RestWebServices/Recall`  ·  **Auth:** none  ·  **Format:** XML by default, add `format=json`

**Questions this notebook answers**
1. What does one recall look like?
2. Which fields hold the model number, lot/date code and UPC — and how often are they filled?
3. When they're not in a field, where are they hiding?

> Saved samples: 20 recalls chosen to match our use cases (baby gear, kids' toys, fire hazards, tip-overs) plus 2 older recalls that have UPCs."""),
("code", SETUP),
("md", """## 1 · Fetch
The API filters by query parameters such as `RecallDateStart`, `RecallDateEnd`, `RecallNumber`, `ProductName`, `Title`.
There is **no paging** — a date window returns every recall in it, so for the backfill we'll walk month by month."""),
("code", """if LIVE:
    recalls = fetch("cpsc", RecallDateStart="2026-09-20", RecallDateEnd="2026-10-20")
    print(len(recalls), "recalls in window")
else:
    recalls = load_samples("cpsc")
print(len(recalls), "records loaded")"""),
("md", "## 2 · Anatomy of one recall\nTop-level keys, then the nested lists. Notice most interesting things are **lists of objects** (`Products`, `Hazards`, `Remedies` …), not plain strings."),
("code", """r = next(x for x in recalls if x["RecallNumber"] == "27027")   # Papablic bedside sleeper (baby gear)
for k, v in r.items():
    if k.startswith("_"): continue
    print(f"{k:<22}", json.dumps(v, ensure_ascii=False)[:110])"""),
("md", "## 3 · Field coverage\nHow often is each field actually filled? This is the single most important table in this notebook."),
("code", """flat = []
for x in recalls:
    p = x["Products"][0] if x["Products"] else {}
    flat.append({**x,
        "Products[].Model": p.get("Model"),
        "Products[].Name": p.get("Name"),
        "Products[].NumberOfUnits": p.get("NumberOfUnits"),
    })
coverage(flat, ["Title", "Description", "Products[].Name", "Products[].Model", "ProductUPCs",
                "Products[].NumberOfUnits", "Manufacturers", "Importers", "Retailers",
                "Hazards", "Remedies", "Images", "Injuries"])"""),
("md", """**Read this carefully.** `Products[].Model` is **0 %** filled. The field exists, but CPSC leaves it blank.
We double-checked this across **93 recalls from three periods** (Sep–Oct 2026, Mar 2024, Jun 2019) during the raw pull: the Model field was empty in every one, and only 2 had `ProductUPCs` (both from 2019).

➡️ **For CPSC, identifiers live in the `Description` prose.** That's why our pipeline needs an extraction step."""),
("md", "## 4 · Where the identifiers hide: regex first pass\n`find_ids()` (in `recall_explore.py`) uses simple patterns like *\"model number X\"*, *\"UPC 1234…\"*, *\"Lot: X\"*. Whatever it misses is the work an LLM has to do."),
("code", """rows = []
for x in recalls:
    ids = find_ids(x["Description"])
    rows.append({"recall": x["RecallNumber"], "tag": x.get("_sample_tag"),
                 "product": x["Products"][0]["Name"][:45] if x["Products"] else "",
                 "models_found": ", ".join(ids["models"]) or "—",
                 "upcs_in_text": len(ids["upcs"]),
                 "upcs_in_field": len(x["ProductUPCs"])})
found = pd.DataFrame(rows).set_index("recall")
found"""),
("code", """has_model = (found.models_found != "—").sum()
print(f"Regex found a model number in {has_model}/{len(found)} descriptions")
print(f"Structured Model field filled in 0/{len(found)}")"""),
("md", """## 5 · The three kinds of CPSC description
Looking at the misses, every recall falls into one of three buckets — each needs a different matching strategy:"""),
("code", """def bucket(x):
    d = x["Description"]
    ids = find_ids(d)
    if re.search(r"(model|item)\\s*(no\\.?|numbers?)[^.]{0,40}(included|following|:)", d, re.I) and len(re.findall(r"\\b[A-Z0-9]{8,}\\b", d)) >= 3:
        return "B · table flattened into prose"
    if ids["models"] or ids["upcs"]:
        return "A · single model in a sentence"
    return "C · no identifier at all"
pd.Series({x["RecallNumber"]: bucket(x) for x in recalls}).value_counts()"""),
("md", """| Bucket | Example | What it means for matching |
|---|---|---|
| **A** single model in a sentence | 27024 *"…thermal laminator, model number TL1302Z"* | Regex/LLM extracts it → exact match on `model_norm` |
| **B** table flattened into prose | 27010 grill brushes, 19131 pendant lights: `Item Number UPC 700TDSTNPSCB-PAR 884655362979 …` | Table structure was lost; an LLM must re-pair model ↔ UPC ↔ date range |
| **C** no identifier | 27020 dresser, 26793 mattress, 27022 medal | Only brand + product name + photo. Needs **semantic match** (embeddings) and the image, and should be shown as *Possible match* |"""),
("code", """for n in ["27010", "27020"]:
    x = next(y for y in recalls if y["RecallNumber"] == n)
    print(n, "→", x["Description"][:420], "\\n")"""),
("md", """## 6 · Other things worth knowing
- **Dates** are ISO strings with a fake time: `2026-10-15T00:00:00`. Parse to `date`.
- `LastPublishDate` changes when a recall is updated → use it to detect updates on re-ingest.
- `Retailers[].Name` often contains *where and when it sold and for how much* — useful for the UI ("Sold on Amazon, 2024–2026, $44–$56").
- `Images[]` has real product photos with captions → great for the results page and for a future image-similarity match.
- Text contains Unicode (™, curly quotes, `\\u2011`) → normalise before matching.
- One `RecallNumber` = one announcement, but it can cover **many models** → confirms the `recalls` 1→* `recall_products` table design."""),
("code", """x = next(y for y in recalls if y["RecallNumber"] == "27024")
print("Retailer:", x["Retailers"][0]["Name"])
print("Image   :", x["Images"][0]["URL"], "-", x["Images"][0]["Caption"])
print("Units   :", x["Products"][0]["NumberOfUnits"])
print("Remedy  :", x["RemedyOptions"])"""),
("md", """## ✅ Takeaways for Recall Radar
1. **Never trust `Products[].Model` or `ProductUPCs`** — extract from `Description` instead.
2. In our 20 samples: 14 name a model/UPC in a sentence (easy), 2 hide a whole table in prose (LLM), and **4 (1 in 5) have no identifier at all** (semantic + photo).
3. Keep the raw JSON (`recalls.raw`) — we'll re-extract when prompts improve.
4. Use `Images`, `Retailers`, `NumberOfUnits` in the UI; they make the result feel trustworthy."""),
])

# =====================================================================  02 openFDA
fda = nb([
("md", """# 02 · openFDA Enforcement API (food · drug · device)

**Agency:** U.S. Food & Drug Administration
**Endpoints:** `https://api.fda.gov/{food|drug|device}/enforcement.json` — same schema for all three
**Auth:** none needed for light use; a free API key raises the daily limit  ·  **Updated:** weekly

> ⚠️ FDA's own disclaimer says this data **should not be used to issue public alerts** or to track a recall's lifecycle, and `status` is **not updated** after classification. Design consequence: food/drug results are a *lookup* with a "confirm on FDA.gov" link, not a push alert.

> Saved samples: 10 food, 5 drug, 5 device — the newest reports (Oct 14 2026)."""),
("code", SETUP),
("md", """## 1 · Fetch
openFDA uses `search=`, `sort=`, `limit=` (max 1000) and `skip=` for paging. Example query language: `search=report_date:[20260901+TO+20261020]`.
`meta.results.total` tells you how many records exist."""),
("code", """if LIVE:
    recalls = []
    for ep, n in [("food", 10), ("drug", 5), ("device", 5)]:
        res = fetch("openfda", endpoint=ep, sort="report_date:desc", limit=n)
        print(ep, "total records:", res["meta"]["results"]["total"])
        recalls += [{**r, "_endpoint": ep} for r in res["results"]]
else:
    recalls = load_samples("openfda")
print(len(recalls), "records loaded")
# Totals seen on 2026-10-20: food 29,505 · drug 18,043 · device 40,300"""),
("md", "## 2 · Anatomy of one record"),
("code", """r = next(x for x in recalls if x["recall_number"] == "H-0016-2027")
for k, v in r.items():
    print(f"{k:<28}", json.dumps(v, ensure_ascii=False)[:110])"""),
("md", """## 3 · Field coverage
Unlike CPSC, almost every field is filled — but the identifiers are packed into **two free-text fields**:
- `product_description` → brand, size, **UPC**, sometimes model / catalog number, NDC
- `code_info` → **lot numbers**, expiry / best-by dates, serials, UDI"""),
("code", """coverage(recalls, ["recall_number", "recalling_firm", "product_description", "code_info",
                   "reason_for_recall", "classification", "status", "distribution_pattern",
                   "product_quantity", "report_date", "openfda"])"""),
("md", "`openfda` is `{}` for nearly every record. It's only populated for some **drugs** (it adds brand names, NDCs and even a UPC list). Don't rely on it."),
("md", "## 4 · Regex first pass on the two text fields"),
("code", """rows = []
for x in recalls:
    pid = find_ids(x["product_description"])
    cid = find_ids(x["code_info"])
    rows.append({"recall": x["recall_number"], "type": x["_endpoint"],
                 "upc (desc)": len(pid["upcs"]), "ndc": len(pid["ndcs"]),
                 "model": ", ".join(pid["models"])[:30] or "—",
                 "lots (code_info)": len(cid["lots"]), "serials": len(cid["serials"]),
                 "udi": len(cid["udis"]), "date codes": len(cid["date_codes"]),
                 "code_info": x["code_info"][:60]})
t = pd.DataFrame(rows).set_index("recall")
t"""),
("code", """for ep in ["food", "drug", "device"]:
    s = t[t.type == ep]
    print(f"{ep:<7} UPC in desc: {(s['upc (desc)']>0).sum()}/{len(s)}   "
          f"lot found: {(s['lots (code_info)']>0).sum()}/{len(s)}   "
          f"date code: {(s['date codes']>0).sum()}/{len(s)}")"""),
("md", """## 5 · The regex is not enough — look at the lists
The lot regex grabs the **first** lot after the word "Lot", but many records list a dozen. Compare what's really there:"""),
("code", """for n in ["D-0006-2027", "Z-0074-2027"]:
    x = next(y for y in recalls if y["recall_number"] == n)
    print(n, "| regex lots:", find_ids(x["code_info"])["lots"])
    print("   real code_info:", x["code_info"][:400], "\\n")"""),
("md", """`D-0006-2027` (dry-eye drops) is the perfect hard case: **9 store brands** (a–i) in `product_description`, each with its own UPC/NDC, and `code_info` maps each letter to its own lots and expiry dates.
An LLM with a strict JSON schema has to rebuild that mapping: `[{brand, upc, lots:[{lot, exp}]}]`."""),
("md", "## 6 · Formats you'll need to normalise"),
("code", """examples = {
  "UPC printed with spaces":   "UPC: 0 75465 11111 0",
  "UPC with ###### wildcard":  "UPC 2 67240 ######  (store-packed weighed item)",
  "Lot with @ suffix":          "LOT: 08032026@24, BUD: 09/17/2026",
  "Date range, not lots":       "Best If Used By Dates from August 14th, 2026 to September 25th, 2026.",
  "'All dates through'":        "Best By: all dates through 3/30/2027",
  "No codes at all":            "no codes",
  "Device serial list":         "Serial numbers: FB00015839, FB00016511, …",
  "Device UDI-DI (GTIN-14)":    "UDI-DI: 00885825003838",
}
for k, v in examples.items():
    print(f"{k:<28} {v:<60} -> upc {find_ids(v)['upcs']}")"""),
("md", """## 7 · Other things worth knowing
- Dates are compact strings `YYYYMMDD` (`"20261014"`). Parse them.
- One **event** (`event_id`) → many `recall_number`s (one per product). E.g. Carolina Infusion event 99867 has 4+ drug recall numbers. Group by `event_id` for the UI.
- `recall_number` can literally be `"N/A"` while a recall is *Not Yet Classified* → use `event_id` + product as a fallback key.
- `classification`: **Class I** = serious health risk / death, II = temporary harm, III = unlikely harm. Great severity signal for alert priority.
- `distribution_pattern` is free text ("FL and NH", "Nationwide") — could power "only alert users in affected states".
- Device recalls are mostly hospital equipment (CT scanners, catheters). Only some (insulin pumps, walkers, home test kits) matter to consumers → filter."""),
("md", """## ✅ Takeaways for Recall Radar
1. **Food is the UPC-rich source** (UPC in 8/10 food descriptions) → barcode scan → exact match is realistic here. Watch for store-packed codes starting with `2` (variable weight, e.g. `2 67240 ######`) — those won't match a shelf barcode.
2. Lots and dates are in `code_info` as messy lists → LLM extraction to `lot_ranges` JSON, keep `code_info` raw.
3. Use `classification` for severity and `event_id` for grouping.
4. Respect FDA's disclaimer: lookup + "verify on FDA.gov", not authoritative alerts. Log this in Decisions."""),
])

# =====================================================================  03 NHTSA
nhtsa = nb([
("md", """# 03 · NHTSA Recalls API (vehicles, tires, car seats, equipment)

**Agency:** National Highway Traffic Safety Administration  ·  **Auth:** none  ·  **Updated:** daily
**Endpoints**
- `https://api.nhtsa.gov/recalls/recallsByVehicle?make=&model=&modelYear=`
- `https://api.nhtsa.gov/recalls/campaignNumber?campaignNumber=`
- Bulk: `FLAT_RCL_POST_2010.zip` (+ data dictionary `RCL.txt`) — best for the full backfill, and the place where **child car seats** and other equipment live.

> Saved samples: 20 recalls across 2018 Honda CR-V, 2021 Ford F-150, 2021 Jeep Wrangler, 2019 Toyota RAV4 — including "park it" / "park outside" flags."""),
("code", SETUP),
("code", """if LIVE:
    recalls = []
    for make, model, yr in [("honda","cr-v",2018), ("ford","f-150",2021), ("jeep","wrangler",2021), ("toyota","rav4",2019)]:
        res = fetch("nhtsa_vehicle", make=make, model=model, modelYear=yr)
        print(make, model, yr, "→", res["Count"], "recalls")
        recalls += res["results"]
else:
    recalls = load_samples("nhtsa")
print(len(recalls), "records loaded")
# Seen on 2026-10-20: CR-V 2018 → 5, F-150 2021 → 29, Wrangler 2021 → 15, RAV4 2019 → 7"""),
("md", "## 1 · Anatomy\nThe cleanest schema of the three: flat, consistent keys, structured make/model/year."),
("code", """r = recalls[0]
for k, v in r.items():
    print(f"{k:<20}", json.dumps(v)[:110])"""),
("code", """coverage(recalls, ["NHTSACampaignNumber", "Manufacturer", "Make", "Model", "ModelYear",
                   "Component", "Summary", "Consequence", "Remedy", "ReportReceivedDate"])"""),
("md", "## 2 · Severity flags\n`parkIt` = don't drive it. `parkOutSide` = fire risk, park away from buildings. `overTheAirUpdate` = fixed by software update."),
("code", """df = pd.DataFrame(recalls)
df[["parkIt", "parkOutSide", "overTheAirUpdate"]].sum()"""),
("code", """df[df.parkIt | df.parkOutSide][["NHTSACampaignNumber", "Make", "Model", "Component", "parkIt", "parkOutSide"]]"""),
("md", """## 3 · Gotcha: the date format is DD/MM/YYYY
`ReportReceivedDate = "25/03/2021"` — day first. Parsing it as US month-first would silently break or swap dates."""),
("code", """df["received"] = pd.to_datetime(df.ReportReceivedDate, format="%d/%m/%Y")
df[["NHTSACampaignNumber", "ReportReceivedDate", "received"]].head()"""),
("md", """## 4 · Gotcha: "your model" ≠ "your car"
A make/model/year query returns every recall that **includes** that model — but the `Summary` usually says *"certain"* vehicles, and many cover a sub-type (hybrid, manual transmission, a production window)."""),
("code", """qualifiers = r"(plug-in|phev|4xe|hybrid|manual transmission|equipped with|built from|manufactured)"
df["narrowed_by"] = df.Summary.str.extract(qualifiers, flags=re.I)[0]
print(f"{df.Summary.str.contains('certain', case=False).sum()}/{len(df)} summaries say 'certain' vehicles")
df[df.narrowed_by.notna()][["NHTSACampaignNumber", "Model", "narrowed_by", "Summary"]].head(8)"""),
("md", """⚠️ Look closely at that table: the qualifier regex is itself misleading. `21V215000` is flagged *Hybrid* only because the Summary lists "MDX Sport Hybrid" — a different model. Deciding *which* qualifier applies to *which* model is, again, a job for LLM extraction, not regex.

Example: `23V787000` comes back for *any* 2021 Wrangler, but it only applies to the **Plug-In Hybrid (4xe)**. If a user owns a gas Wrangler, that would be a false alarm.
Only the VIN-level check on NHTSA.gov knows whether a *specific* car is affected **and still unrepaired**. So:
- Our VIN feature = decode VIN → make/model/year/trim → show recalls **for the model**, clearly labelled, + deep-link to NHTSA's official VIN check.
- One campaign shows up under **many** models (`21V215000` fuel pump covers ~20 Honda/Acura models) → store campaign once, link many vehicles."""),
("code", """df.groupby("Component").size().sort_values(ascending=False).head(10)"""),
("md", """Note `EQUIPMENT:OTHER:LABELS` — a sticker/label recall. Those are real but low-stakes; rank them below airbags and brakes."""),
("md", """## ✅ Takeaways for Recall Radar
1. NHTSA is the **easiest to ingest** (clean, structured) — great first data source for the week-4 MVP.
2. Parse `ReportReceivedDate` as **DD/MM/YYYY**.
3. Use `parkIt` / `parkOutSide` for top-priority alerts, `Component` for severity tiers.
4. Model-level matching over-matches (trims, hybrids). Be honest in the UI and link to NHTSA's VIN check.
5. Car seats come from NHTSA's **bulk file**, not the vehicle endpoint → add a backfill task for it."""),
])

# =====================================================================  04 Findings
findings = nb([
("md", """# 04 · Findings & field map (the one-page summary)

This notebook pulls the three explorations together into the table you'll design the schema and extraction prompts from."""),
("code", SETUP),
("code", """cpsc, fda, nh = load_samples("cpsc"), load_samples("openfda"), load_samples("nhtsa")

def pct(n, d): return f"{n}/{d} ({round(100*n/d)}%)"

cpsc_model = sum(1 for r in cpsc if find_ids(r["Description"])["models"])
cpsc_struct = sum(1 for r in cpsc for p in r["Products"] if p.get("Model"))
cpsc_upc = sum(1 for r in cpsc if r["ProductUPCs"])
food = [r for r in fda if r["_endpoint"] == "food"]
fda_upc = sum(1 for r in fda if find_ids(r["product_description"])["upcs"])
food_upc = sum(1 for r in food if find_ids(r["product_description"])["upcs"])
fda_lot = sum(1 for r in fda if find_ids(r["code_info"])["lots"])
fda_codes = sum(1 for r in fda if r["code_info"].strip().lower() not in ("no codes", "n/a", ""))

pd.DataFrame({
  "CPSC (20)": ["Description prose", pct(cpsc_struct, 20) + " structured · " + pct(cpsc_model, 20) + " in prose",
                pct(cpsc_upc, 20) + " (only 2019 recalls)", "dates/lots rare, in prose", "XML/JSON, no key, no paging"],
  "openFDA (20)": ["product_description + code_info", "devices only (catalog #)",
                   pct(fda_upc, 20) + " · food " + pct(food_upc, len(food)), pct(fda_lot, 20) + " regex · " + pct(fda_codes, 20) + " have codes",
                   "JSON, optional key, limit/skip paging, weekly"],
  "NHTSA (20)": ["Make/Model/ModelYear fields", "100% structured (vehicle level)", "n/a", "n/a (VIN-level only on nhtsa.gov)",
                 "JSON, no key, daily + bulk zip"],
}, index=["Where identifiers live", "Model #", "UPC", "Lot / serial / date", "Access"])"""),
("md", """## Decisions this exploration triggers
| # | Decision | Why (evidence) |
|---|---|---|
| 1 | **Extract identifiers from prose with an LLM**, regex as pre-filter | CPSC `Model` field empty in 93/93 recalls checked; openFDA lots are multi-item lists |
| 2 | **Keep raw payloads** in `recalls.raw` and re-extract when prompts improve | Formats vary wildly; extraction will get better over time |
| 3 | **Three match tiers**: exact (model/UPC), structured (vehicle), semantic (brand+product+photo) | 4 of 20 CPSC samples (1 in 5) have no identifier at all |
| 4 | **openFDA = lookup, not alert** source; link to FDA.gov | FDA disclaimer: not for public alerts; status not updated |
| 5 | **VIN = decode → model-level recalls + link to official VIN check** | Model query over-matches trims (e.g. 4xe-only recalls) |
| 6 | **Car seats from NHTSA bulk file** | Not reachable via recallsByVehicle |
| 7 | Use **severity signals**: FDA `classification`, NHTSA `parkIt`/`parkOutSide`, CPSC hazard text | Prioritise alerts |

## Schema tweaks to make in week 2
- `recall_products.lot_ranges` → store a list of `{lot, exp_date}` **and** date-range objects `{from, to, kind:"best_by"}`.
- Add `recall_products.udi` / `ndc` (devices & drugs) and `recalls.severity` (normalised from the three sources).
- Add `recalls.event_id` (openFDA grouping) and `recall_vehicles` (one campaign → many make/model/year rows)."""),
("code", """# The normaliser that will produce recall_products.model_norm — and its first unit-test cases
cases = {"TL1302Z": "TL1302Z", "7927-OZ1": "7927OZ1", "RWX-RBP02": "RWXRBP02", "xj-200 b": "XJ200B",
         "MMT-8062": "MMT8062", "PAPA03001AI": "PAPA03001AI"}
for raw, expected in cases.items():
    got = normalize_model(raw)
    print(f"{raw:<12} -> {got:<12} {'✓' if got == expected else '✗ expected ' + expected}")"""),
])

for name, n in [("01_cpsc.ipynb", cpsc), ("02_openfda.ipynb", fda), ("03_nhtsa.ipynb", nhtsa), ("04_findings.ipynb", findings)]:
    nbf.write(n, NB / name)
    print("wrote", name)
