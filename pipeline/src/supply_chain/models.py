from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Country(str, Enum):
    AUSTRALIA = "AU"
    CHINA = "CN"
    UNITED_STATES = "US"
    OTHER = "OTHER"


class RelationType(str, Enum):
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    PARTNER = "partner"
    UNDISCLOSED_SUPPLIER = "undisclosed_supplier"
    UNDISCLOSED_CUSTOMER = "undisclosed_customer"


class ConfidenceBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CompanySeed(BaseModel):
    country: Country
    rank: int
    name: str
    ticker: str = ""
    exchange: str = ""
    market_cap_usd_billions: float | None = None
    source_url: str
    profile_url: str
    statement_search_name: str = ""
    annual_report_url: str = ""
    cik: str = ""


class SourceDocument(BaseModel):
    document_id: str
    country: Country
    company_name: str
    source_system: str
    document_type: str
    title: str
    filing_year: int | None = None
    filing_date: str = ""
    download_url: str
    local_path: str
    metadata_path: str = ""


class ParsedEvidence(BaseModel):
    evidence_id: str
    country: Country
    relation_type: RelationType
    reporter_name: str
    counterparty_name: str = ""
    counterparty_country: Country | None = None
    confidence: ConfidenceBand
    source_system: str
    document_id: str
    document_title: str
    excerpt: str
    page_reference: str = ""
    filing_year: int | None = None
    amount_text: str = ""
    percentage_text: str = ""
    parser_method: str
    named_counterparty: bool = True
    download_url: str = ""
    local_path: str = ""


class NormalizedEntity(BaseModel):
    entity_id: str
    display_name: str
    country: Country
    aliases: list[str] = Field(default_factory=list)
    source_ids: dict[str, str] = Field(default_factory=dict)
    node_kind: Literal["company", "placeholder"] = "company"


class NormalizedEdge(BaseModel):
    edge_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    confidence: ConfidenceBand
    evidence_ids: list[str]
    countries: list[Country]
    source_systems: list[str]
    explicit: bool = True


class CandidateLink(BaseModel):
    candidate_link_id: str
    undisclosed_entity_id: str
    candidate_entity_id: str
    rank: int
    confidence: ConfidenceBand
    rationale: str
    supporting_evidence_ids: list[str]


class GraphNode(BaseModel):
    id: str
    label: str
    country: Country
    node_kind: Literal["company", "placeholder"] = "company"
    aliases: list[str] = Field(default_factory=list)
    source_ids: dict[str, str] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation_type: RelationType
    confidence: ConfidenceBand
    explicit: bool = True
    evidence_ids: list[str]


class GraphBundle(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    evidence: list[ParsedEvidence]
    candidates: list[CandidateLink]
    sources: dict[str, list[str]]
