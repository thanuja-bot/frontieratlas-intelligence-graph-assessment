"""Canonical output schemas used by the demo and live adapters."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PricingModel(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"
    PAID = "PAID"
    ENTERPRISE = "ENTERPRISE"


class StartupRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schemaVersion: str = "1.0"
    recordType: str = "STARTUP"
    source_name: str = Field(alias="source.name")
    source_url: str = Field(alias="source.url")
    entity_name: str = Field(alias="content.entityName")
    employee_count: int = Field(alias="content.data.employeeCount")
    collected_at: datetime = Field(default_factory=utc_now, alias="collectedAt")


class ProductRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schemaVersion: str = "1.0"
    recordType: str = "PRODUCT"
    source_name: str = Field(alias="source.name")
    source_url: str = Field(alias="source.url")
    startup_name: str = Field(alias="content.startupName")
    product_name: str = Field(alias="content.productName")
    pricing_model: PricingModel = Field(alias="content.pricingModel")
    collected_at: datetime = Field(default_factory=utc_now, alias="collectedAt")


class ResearchPaperRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schemaVersion: str = "1.0"
    recordType: str = "RESEARCH_PAPER"
    source_name: str = Field(alias="source.name")
    source_url: str = Field(alias="source.url")
    title: str = Field(alias="content.title")
    authors: List[str] = Field(alias="content.authors")
    paper_url: str = Field(alias="content.paper_url")
    github_url: Optional[str] = Field(alias="content.github_url")
    github_stars: int = Field(alias="content.github_stars", ge=0)
    published_date: datetime = Field(alias="content.published_date")
    collected_at: datetime = Field(default_factory=utc_now, alias="collectedAt")


class JobRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schemaVersion: str = "1.0"
    recordType: str = "JOB"
    source_name: str = Field(alias="source.name")
    source_url: str = Field(alias="source.url")
    company: str = Field(alias="content.company")
    date: datetime = Field(alias="content.date")
    is_remote: bool = Field(alias="content.is_remote")
    role_family: str = Field(alias="content.role_family")
    title: str = Field(alias="content.title")
    collected_at: datetime = Field(default_factory=utc_now, alias="collectedAt")


class NewsRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schemaVersion: str = "1.0"
    recordType: str = "NEWS"
    source_name: str = Field(alias="source.name")
    source_url: str = Field(alias="source.url")
    headline: str = Field(alias="content.headline")
    company: str = Field(alias="content.company")
    published_at: datetime = Field(alias="content.publishedAt")
    body: str = Field(alias="content.body")
    collected_at: datetime = Field(default_factory=utc_now, alias="collectedAt")


class EntityMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_name: str
    canonical_name: str
    confidence: float
    match_method: str
    entity_type: str