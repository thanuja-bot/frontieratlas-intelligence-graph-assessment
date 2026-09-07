# FrontierAtlas Intelligence Graph assessment

This repository contains a runnable, asynchronous ingestion pipeline for the GraphOne / FrontierAtlas
AI intelligence-graph assessment. It produces the six requested CSV exports and a three-page
`architecture.pdf`.

## Important data-integrity note

The default run is **deterministic fixture mode**. It is intentionally reproducible for review and
offline execution, and every generated row is marked by a source name containing `fixture`. It must not
be presented as verified live intelligence. The adapters and schema contracts are structured so live
providers can replace fixtures without changing the orchestrator or exports.

`--live-arxiv` enables the included public arXiv API adapter. Startup/product/news/job adapters remain
fixtures until each source has been approved and implemented with its terms, rate limits, evidence
retention, and date parsing rules.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python run_pipeline.py
python run_pipeline.py --count 1000 --live-arxiv
```

Outputs are written to `output/`:

- `startups.csv` — 1,000 startup records
- `products.csv` — 1,000 product records with pricing enums
- `research_papers.csv` — 1,000 paper records with ISO timestamps and GitHub metrics
- `jobs.csv` — 1,000 fresh job fixtures across five board families
- `news.csv` — 1,000 fresh news fixtures across five source families
- `entity_mapping_log.csv` — raw-to-canonical organization mappings
- `run_metadata.json` — mode and row-count manifest

The command validates minimum row counts, source URLs, and the 24-hour news freshness rule before
building `architecture.pdf`.

## Architecture

- `src/scrapers/` contains async source adapters and fixture/live boundaries.
- `src/llm/extractor.py` implements Gemini Flash → Groq → DeepSeek fallback, 413 chunking, and 429
  exponential backoff with jitter.
- `src/resolver/entity_resolver.py` uses a 50-company canonical seed list and RapidFuzz.
- `src/schemas.py` contains typed Pydantic output contracts.
- `architecture.md` is the readable design document; `architecture.pdf` is the submission artifact.

## Production path

For a live submission, replace each fixture method with a compliant adapter that stores immutable raw
evidence, parses absolute/relative dates in UTC, checks source freshness, and rejects records without
traceable evidence. Scale by partitioning source cursors and running the stateless workers behind a
queue; see `architecture.md` for the 500k+ record design, Redis URL-hash leases, PostgreSQL/pgvector
storage, anti-bot boundaries, and operational metrics.