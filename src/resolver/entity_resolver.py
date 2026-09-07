"""Deterministic fuzzy organization resolution against a 50-name seed list."""

from __future__ import annotations

import re
from typing import Iterable, List, Tuple

from rapidfuzz import fuzz, process

from src.schemas import EntityMapping
from src.scrapers.directory_scraper import CANONICAL_STARTUPS


def normalize(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"\b(incorporated|inc|llc|ltd|corp|corporation)\b", "", value)
    return re.sub(r"[^a-z0-9]+", "", value)


class EntityResolver:
    def __init__(self, canonical_names: Iterable[str] = CANONICAL_STARTUPS) -> None:
        self.canonical_names = list(canonical_names)
        self.normalized = {normalize(name): name for name in self.canonical_names}

    def resolve(self, raw_name: str, entity_type: str = "STARTUP") -> Tuple[str, float, str]:
        normalized = normalize(raw_name)
        if normalized in self.normalized:
            return self.normalized[normalized], 100.0, "exact_normalized"
        match = process.extractOne(
            normalized,
            list(self.normalized.keys()),
            scorer=fuzz.ratio,
        )
        if not match:
            return raw_name, 0.0, "unresolved"
        key, score, _ = match
        if score < 72:
            return raw_name, float(score), "below_threshold"
        return self.normalized[key], float(score), "rapidfuzz_ratio"

    def map_names(self, names: Iterable[str], entity_type: str = "STARTUP") -> List[EntityMapping]:
        return [
            EntityMapping(
                raw_name=name,
                canonical_name=self.resolve(name, entity_type)[0],
                confidence=round(self.resolve(name, entity_type)[1], 2),
                match_method=self.resolve(name, entity_type)[2],
                entity_type=entity_type,
            )
            for name in names
        ]