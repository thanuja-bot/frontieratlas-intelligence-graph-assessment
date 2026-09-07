"""Research-paper adapter.

The default fixture adapter is deterministic so the assessment can be run
offline. ArxivAdapter is intentionally kept behind the same async interface;
it can be enabled when a live run is requested and credentials/network policy
allow it.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from src.schemas import ResearchPaperRecord


class ArxivScraper:
    def __init__(self, count: int = 1000, live: bool = False) -> None:
        self.count = count
        self.live = live

    async def fetch(self) -> List[ResearchPaperRecord]:
        if self.live:
            return await self._fetch_live()
        return await self._generate_fixture()

    async def _generate_fixture(self) -> List[ResearchPaperRecord]:
        topics = [
            "language models", "multimodal learning", "robotics", "alignment",
            "computer vision", "generative modeling", "retrieval", "agents",
        ]
        now = datetime.now(timezone.utc)
        records: List[ResearchPaperRecord] = []
        for i in range(1, self.count + 1):
            topic = topics[(i - 1) % len(topics)]
            paper_id = f"2601.{i:05d}"
            records.append(
                ResearchPaperRecord(
                    **{
                        "source.name": "arXiv (deterministic assessment fixture)",
                        "source.url": "https://arxiv.org/",
                        "content.title": f"Frontier Study {i:04d}: {topic.title()}",
                        "content.authors": [
                            f"Researcher {(i % 97) + 1}",
                            f"Researcher {(i % 53) + 2}",
                        ],
                        "content.paper_url": f"https://arxiv.org/abs/{paper_id}",
                        "content.github_url": f"https://github.com/frontieratlas/paper-{i:04d}",
                        "content.github_stars": (i * 37) % 24500,
                        "content.published_date": now - timedelta(days=(i % 365)),
                    }
                )
            )
            if i % 100 == 0:
                await asyncio.sleep(0)
        return records

    async def _fetch_live(self) -> List[ResearchPaperRecord]:
        """Fetch a small live sample from the public arXiv API.

        The fixture mode remains the reproducible assessment path. This live
        adapter deliberately returns only records that came from arXiv and
        leaves GitHub enrichment as a separate production concern.
        """
        query = "cat:cs.AI"
        url = "https://export.arxiv.org/api/query"
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(
                url, params={"search_query": query, "start": 0, "max_results": self.count}
            )
            response.raise_for_status()
        # XML parsing is intentionally dependency-free for the live smoke path.
        import xml.etree.ElementTree as ET

        root = ET.fromstring(response.text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        records = []
        for entry in root.findall("a:entry", ns):
            paper_url = (entry.findtext("a:id", default="", namespaces=ns)).strip()
            title = " ".join((entry.findtext("a:title", default="", namespaces=ns)).split())
            published = entry.findtext("a:published", default="", namespaces=ns)
            authors = [
                a.findtext("a:name", default="", namespaces=ns)
                for a in entry.findall("a:author", ns)
            ]
            records.append(
                ResearchPaperRecord(
                    **{
                        "source.name": "arXiv",
                        "source.url": "https://export.arxiv.org/api/query",
                        "content.title": title,
                        "content.authors": authors,
                        "content.paper_url": paper_url,
                        "content.github_url": None,
                        "content.github_stars": 0,
                        "content.published_date": published,
                    }
                )
            )
        return records