"""Multi-tier extraction with explicit 413 chunking and 429 backoff."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Protocol


class PayloadTooLargeError(Exception):
    """Provider rejected an input payload as too large (HTTP 413 equivalent)."""


class RateLimitError(Exception):
    """Provider requested a retry (HTTP 429 equivalent)."""


class Provider(Protocol):
    name: str

    async def extract(self, text: str) -> Dict[str, Any]:
        ...


def chunk_text(text: str, max_chars: int = 12_000, overlap: int = 500) -> List[str]:
    """Split on a hard character budget while retaining boundary context."""
    if max_chars <= overlap:
        raise ValueError("max_chars must be greater than overlap")
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    step = max_chars - overlap
    while start < len(text):
        chunks.append(text[start : start + max_chars])
        start += step
    return chunks


@dataclass
class MockProvider:
    name: str
    max_chars: int = 12_000
    fail_429_times: int = 0
    calls: int = 0

    async def extract(self, text: str) -> Dict[str, Any]:
        self.calls += 1
        if len(text) > self.max_chars:
            raise PayloadTooLargeError(f"{self.name}: {len(text)} > {self.max_chars}")
        if self.fail_429_times > 0:
            self.fail_429_times -= 1
            raise RateLimitError(f"{self.name}: simulated rate limit")
        return {
            "provider": self.name,
            "text_length": len(text),
            "entities": [{"type": "SIGNAL", "value": text[:80].strip()}],
        }


class ExtractionOrchestrator:
    def __init__(
        self,
        providers: Iterable[Provider] | None = None,
        max_chars: int = 12_000,
        max_retries: int = 4,
        base_delay: float = 0.05,
    ) -> None:
        self.providers = list(
            providers
            or [
                MockProvider("Gemini Flash"),
                MockProvider("Groq Llama 3"),
                MockProvider("DeepSeek"),
            ]
        )
        self.max_chars = max_chars
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def extract(self, text: str) -> Dict[str, Any]:
        chunks = chunk_text(text, self.max_chars)
        errors: List[str] = []
        for provider in self.providers:
            results = []
            try:
                for chunk in chunks:
                    results.append(await self._call_with_backoff(provider, chunk))
                return {
                    "provider": getattr(provider, "name", provider.__class__.__name__),
                    "chunks": results,
                    "chunk_count": len(chunks),
                }
            except (PayloadTooLargeError, RateLimitError) as exc:
                errors.append(f"{getattr(provider, 'name', 'provider')}: {exc}")
        raise RuntimeError("all extraction tiers failed: " + " | ".join(errors))

    async def _call_with_backoff(self, provider: Provider, chunk: str) -> Dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            try:
                return await provider.extract(chunk)
            except PayloadTooLargeError:
                # This should be prevented by chunk_text; don't retry an invalid request.
                raise
            except RateLimitError:
                if attempt >= self.max_retries:
                    raise
                delay = self.base_delay * (2**attempt) + random.uniform(0, self.base_delay)
                await asyncio.sleep(delay)
        raise AssertionError("unreachable")