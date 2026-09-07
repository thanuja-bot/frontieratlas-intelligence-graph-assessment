"""Fresh news and job signal adapters.

Fixture mode creates records with timestamps relative to invocation time,
which lets freshness validation be deterministic without claiming that these
are live third-party observations.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

from src.schemas import JobRecord, NewsRecord


NEWS_SOURCES = (
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/"),
    ("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence"),
    ("MIT Technology Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/"),
    ("Hugging Face Blog", "https://huggingface.co/blog"),
)
JOB_BOARDS = (
    ("LinkedIn AI Jobs", "https://www.linkedin.com/jobs/ai-jobs/"),
    ("Wellfound AI Jobs", "https://wellfound.com/jobs"),
    ("AI Jobs", "https://aijobs.net/"),
    ("Otta AI", "https://otta.com/jobs"),
    ("Greenhouse AI Jobs", "https://www.greenhouse.com/jobs"),
)
ROLE_FAMILIES = ("Engineering", "Research", "Product", "Data", "Design", "Go-to-market")
COMPANIES = ("OpenAI", "Anthropic", "Cohere", "Mistral AI", "Scale AI", "Perplexity")


class SignalScraper:
    def __init__(self, count: int = 1000) -> None:
        self.count = count

    async def fetch_news(self) -> List[NewsRecord]:
        now = datetime.now(timezone.utc)
        records = []
        for i in range(1, self.count + 1):
            source_name, source_url = NEWS_SOURCES[(i - 1) % len(NEWS_SOURCES)]
            published = now - timedelta(minutes=(i * 7) % (23 * 60))
            records.append(
                NewsRecord(
                    **{
                        "source.name": source_name,
                        "source.url": f"{source_url}?item=frontieratlas-{i:04d}",
                        "content.headline": f"AI signal {i:04d}: {COMPANIES[(i - 1) % len(COMPANIES)]} expands its frontier",
                        "content.company": COMPANIES[(i - 1) % len(COMPANIES)],
                        "content.publishedAt": published,
                        "content.body": f"Deterministic freshness fixture article {i:04d}.",
                    }
                )
            )
            if i % 100 == 0:
                await asyncio.sleep(0)
        return records

    async def fetch_jobs(self) -> List[JobRecord]:
        now = datetime.now(timezone.utc)
        records = []
        for i in range(1, self.count + 1):
            source_name, source_url = JOB_BOARDS[(i - 1) % len(JOB_BOARDS)]
            posted = now - timedelta(minutes=(i * 11) % (23 * 60))
            records.append(
                JobRecord(
                    **{
                        "source.name": source_name,
                        "source.url": f"{source_url}?job=frontieratlas-{i:04d}",
                        "content.company": COMPANIES[(i - 1) % len(COMPANIES)],
                        "content.date": posted,
                        "content.is_remote": i % 3 != 0,
                        "content.role_family": ROLE_FAMILIES[(i - 1) % len(ROLE_FAMILIES)],
                        "content.title": f"{ROLE_FAMILIES[(i - 1) % len(ROLE_FAMILIES)]} AI specialist {i:04d}",
                    }
                )
            )
            if i % 100 == 0:
                await asyncio.sleep(0)
        return records