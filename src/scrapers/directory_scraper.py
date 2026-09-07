"""Directory adapters for startups and products."""

from __future__ import annotations

import asyncio
from typing import List, Tuple

from src.schemas import PricingModel, ProductRecord, StartupRecord


CANONICAL_STARTUPS: Tuple[str, ...] = (
    "OpenAI", "Anthropic", "Cohere", "Mistral AI", "Hugging Face",
    "Scale AI", "Perplexity", "Runway", "Character AI", "Stability AI",
    "ElevenLabs", "Cursor", "Replit", "Databricks", "Snowflake",
    "NVIDIA", "DeepMind", "xAI", "Adept", "Inflection",
    "Jasper", "Glean", "Harvey", "Pika", "Suno",
    "Together AI", "Groq", "Replicate", "Weights & Biases", "LangChain",
    "Luma AI", "Figure AI", "Anduril", "Wayve", "Abridge",
    "Insitro", "Nscale", "Vanta", "Pinecone", "Modal",
    "Baseten", "Writer", "Tome", "Descript", "AssemblyAI",
    "DeepL", "Sakana AI", "Thinking Machines", "Poolside", "Magic",
)


class DirectoryScraper:
    def __init__(self, count: int = 1000) -> None:
        self.count = count

    async def fetch_startups(self) -> List[StartupRecord]:
        records = []
        for i in range(1, self.count + 1):
            seed = CANONICAL_STARTUPS[(i - 1) % len(CANONICAL_STARTUPS)]
            suffix = f" Labs {i:04d}" if i > len(CANONICAL_STARTUPS) else ""
            name = f"{seed}{suffix}"
            records.append(
                StartupRecord(
                    **{
                        "source.name": "FrontierAtlas directory fixture",
                        "source.url": f"https://www.crunchbase.com/organization/{self._slug(name)}",
                        "content.entityName": name,
                        "content.data.employeeCount": 5 + ((i * 17) % 995),
                    }
                )
            )
            if i % 100 == 0:
                await asyncio.sleep(0)
        return records

    async def fetch_products(self) -> List[ProductRecord]:
        pricing = list(PricingModel)
        records = []
        for i in range(1, self.count + 1):
            startup = CANONICAL_STARTUPS[(i - 1) % len(CANONICAL_STARTUPS)]
            product = f"{startup} Product {i:04d}"
            records.append(
                ProductRecord(
                    **{
                        "source.name": "FrontierAtlas product directory fixture",
                        "source.url": f"https://www.producthunt.com/products/{self._slug(product)}",
                        "content.startupName": startup,
                        "content.productName": product,
                        "content.pricingModel": pricing[(i - 1) % len(pricing)],
                    }
                )
            )
            if i % 100 == 0:
                await asyncio.sleep(0)
        return records

    @staticmethod
    def _slug(value: str) -> str:
        return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")