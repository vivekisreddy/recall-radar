# Decisions

Why the project is built the way it is. Newest first. Add a row when you make a choice someone could reasonably question.

| # | Date | Decision | Alternatives considered | Why |
|---|---|---|---|---|
| 12 | 2026-11-08 | Self-host the Geist font via the `geist` npm package | `next/font/google` | Builds (Docker, CI) never depend on reaching Google Fonts. |
| 11 | 2026-11-08 | Web fetches the API from Server Components with a server-only `API_URL` | `NEXT_PUBLIC_API_URL` + client fetching | URL is read at request time (one image, many environments) and never shipped to the browser. |
| 10 | 2026-11-08 | `matches` points at `recalls` (required) and `recall_products` (optional) | Only `recall_product_id` | Vehicle matches go through `recall_vehicles`, not products; one table holds both. |
| 9 | 2026-11-08 | Tests run Alembic migrations against a real Postgres + pgvector | SQLite or `create_all()` | A broken migration or pgvector index fails CI instead of production. |
| 8 | 2026-11-08 | One Python package for API and workers (`backend/`) | Separate `api/` and `workers/` projects | They share models and the data pipeline; one image, three commands. |
| 7 | 2026-10-20 | One `severity` scale across agencies | Keep each agency's own field | FDA Class I/II/III, NHTSA park-it flags and CPSC hazard text need one ranking for alerts. |
| 6 | 2026-10-20 | Child car seats come from NHTSA's bulk file | The vehicle endpoint | The vehicle endpoint doesn't cover equipment recalls. |
| 5 | 2026-10-20 | VIN lookup = decode, then model-level recalls, plus a link to NHTSA's VIN check | Claim per-car results | A make/model/year query over-matches trims (e.g. plug-in-hybrid-only recalls). |
| 4 | 2026-10-20 | openFDA is a lookup source, not an alert source | Push FDA alerts | FDA's disclaimer says the data must not drive public alerts; status isn't updated. |
| 3 | 2026-10-20 | Three match tiers: exact (model/UPC), structured (vehicle), semantic (brand + product + photo) | Exact matching only | 1 in 5 CPSC recalls has no model or UPC at all. |
| 2 | 2026-10-20 | Keep every raw payload in `recalls.raw`; re-extract when prompts improve | Store only parsed fields | Formats vary wildly; extraction will get better over time. |
| 1 | 2026-10-20 | Extract identifiers from prose with an LLM (strict JSON schema), regex as pre-filter | Use agency fields directly | CPSC's `Model` field was empty in 93/93 recalls; openFDA lots are multi-item lists. |
| 0 | 2026-10-12 | FastAPI, Postgres + pgvector, Redis + Celery, Next.js PWA | Django; Pinecone; React Native | Same language as the ML code; one database for relational, fuzzy and vector search; camera works in the browser without an app store. |

Evidence for decisions 1–7: [research/api-exploration](../research/api-exploration/README.md).
