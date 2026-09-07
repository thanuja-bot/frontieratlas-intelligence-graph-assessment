# FrontierAtlas Intelligence Graph — architecture

## Scope and data integrity

The repository defaults to deterministic fixture mode so the assessment can be reviewed without live
third-party access. This is a test harness, not a claim that fixture rows are observed from the web.
The live adapter boundary is explicit: a production run must persist raw evidence, retain the source
URL, and reject unverified rows.

## Scale strategy: 500k+ records

Partition by source and source cursor/range. A coordinator puts idempotent fetch tasks on a queue;
stateless asyncio workers use connection pooling, per-host semaphores, and backpressure. Persist raw
responses to object storage under `sha256(normalized_url)/fetch_timestamp`, then run extraction and
entity resolution as independently scalable stages. Checkpoints include source, cursor, response
checksum, parser version, and schema version. Adding workers and queue partitions scales the run
without changing adapter code.

## LLM extraction: 413 and 429

Measure payload size before each request and split text into 12,000-character chunks with 500-character
overlap. Merge chunk results by stable entity keys. A 413 is an input error: rechunk once and never
retry the same oversized request. A 429 honors `Retry-After` when supplied; otherwise it uses bounded
exponential backoff with jitter and a per-provider token bucket. Exhausted requests fall through
Gemini Flash → Groq Llama 3 → DeepSeek. Provider, attempt, status, and payload hash are logged.

## Freshness and anti-bot strategy

Normalize the canonical URL and acquire a Redis lease with `SET NX` using its SHA-256 hash. Store
`last_seen_published_at`, response checksum, and source cursor. Parse absolute and relative dates in
UTC and enforce a 24-hour watermark after parsing. Missing or ambiguous dates go to review rather
than being labeled fresh. Prefer official APIs/RSS. For JavaScript-heavy or protected domains, use
an approved Playwright worker, low host concurrency, caching, and terms-compliant access. Never
attempt CAPTCHA circumvention; use a compliant fallback or human review.

## Storage

PostgreSQL is the system of record: transactions, constraints, JSONB for source-specific fields, and
upserts for entity versions. `pgvector` supports semantic candidate retrieval, while deterministic
RapidFuzz matching remains the final canonicalization gate. Relationship tables connect startups,
products, papers, jobs, news, founders, and sources. Redis handles leases/rate limits/freshness
watermarks; object storage keeps immutable HTML/JSON evidence. Every row carries source URL,
`collectedAt`, parser version, and evidence checksum.

## Contracts and operations

Pydantic validates `schemaVersion`, `recordType`, required fields, enum values, non-negative metrics,
and ISO-8601 timestamps. Metrics include fetch success, freshness pass rate, duplicates, unresolved
entities, provider fallback, and queue latency. Secrets are environment-injected and excluded from
logs/exports. CSV is a review export; typed persistence is the production source of truth.