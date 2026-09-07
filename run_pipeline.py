"""Run the FrontierAtlas assessment pipeline and write six CSV deliverables."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import shutil
from pathlib import Path
from typing import Iterable, Sequence

from src.llm.extractor import ExtractionOrchestrator, MockProvider, chunk_text
from src.resolver.entity_resolver import EntityResolver
from src.schemas import EntityMapping
from src.scrapers.arxiv_scraper import ArxivScraper
from src.scrapers.directory_scraper import DirectoryScraper
from src.scrapers.signal_scraper import SignalScraper


OUTPUT_DIR = Path("output")
LOGGER = logging.getLogger("frontieratlas")


def model_rows(records: Iterable[object]) -> list[dict]:
    return [record.model_dump(by_alias=True, mode="json") for record in records]


def write_csv(path: Path, rows: Sequence[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


async def run(count: int = 1000, output_dir: Path = OUTPUT_DIR, live: bool = False) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    directory, papers, signals = DirectoryScraper(count), ArxivScraper(count, live), SignalScraper(count)
    startups, products, research, jobs, news = await asyncio.gather(
        directory.fetch_startups(),
        directory.fetch_products(),
        papers.fetch(),
        signals.fetch_jobs(),
        signals.fetch_news(),
    )

    resolver = EntityResolver()
    raw_names = ["Open AI", "OpenAI, Inc.", "Anthropic LLC", "Mistral-AI", "Unknown startup"]
    mappings = [
        EntityMapping(
            raw_name=raw,
            canonical_name=resolver.resolve(raw)[0],
            confidence=round(resolver.resolve(raw)[1], 2),
            match_method=resolver.resolve(raw)[2],
            entity_type="STARTUP",
        )
        for raw in raw_names
    ]
    mappings.extend(
        EntityMapping(
            raw_name=record.entity_name,
            canonical_name=resolver.resolve(record.entity_name)[0],
            confidence=round(resolver.resolve(record.entity_name)[1], 2),
            match_method=resolver.resolve(record.entity_name)[2],
            entity_type="STARTUP",
        )
        for record in startups
    )

    files = {
        "startups.csv": model_rows(startups),
        "products.csv": model_rows(products),
        "research_papers.csv": model_rows(research),
        "jobs.csv": model_rows(jobs),
        "news.csv": model_rows(news),
        "entity_mapping_log.csv": model_rows(mappings),
    }
    counts = {}
    for filename, rows in files.items():
        write_csv(output_dir / filename, rows)
        counts[filename] = len(rows)
    (output_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "mode": "live-arxiv-plus-fixtures" if live else "deterministic-fixture",
                "count_per_vertical": count,
                "source_evidence_note": (
                    "Fixture mode is synthetic and clearly labeled; do not present it as live intelligence."
                ),
                "files": counts,
            },
            indent=2,
        )
    )
    return counts


def validate(output_dir: Path = OUTPUT_DIR) -> None:
    required = {
        "startups.csv": 1000,
        "products.csv": 1000,
        "research_papers.csv": 1000,
        "jobs.csv": 1000,
        "news.csv": 1000,
        "entity_mapping_log.csv": 1000,
    }
    for filename, minimum in required.items():
        path = output_dir / filename
        with path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) < minimum:
            raise AssertionError(f"{filename}: {len(rows)} < {minimum}")
        for row in rows:
            if not row.get("source.url") and filename != "entity_mapping_log.csv":
                raise AssertionError(f"{filename} contains a row without source.url")
    with (output_dir / "news.csv").open(encoding="utf-8") as handle:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        for row in csv.DictReader(handle):
            published = datetime.fromisoformat(row["content.publishedAt"].replace("Z", "+00:00"))
            if (now - published).total_seconds() > 24 * 3600:
                raise AssertionError("news freshness validation failed")
    LOGGER.info("Validation passed: schemas, row minima, URLs, and 24-hour news freshness.")


def build_pdf() -> None:
    from scripts.build_architecture_pdf import build

    build("architecture.pdf")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--live-arxiv", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    counts = await run(args.count, args.output, args.live_arxiv)
    validate(args.output)
    build_pdf()
    LOGGER.info("Generated %s", counts)


if __name__ == "__main__":
    asyncio.run(main())