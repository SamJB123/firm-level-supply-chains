from __future__ import annotations

import hashlib
import re
from pathlib import Path

from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType, SourceDocument
from supply_chain.normalize.entities import normalize_name
from supply_chain.parsers.pdf_text import extract_text_from_pdf


SUPPLY_CONTEXT_KEYWORDS = (
    "supplier",
    "suppliers",
    "customer",
    "customers",
    "foundries",
    "contract manufacturers",
    "assembly",
    "manufacturing",
    "purchase from",
    "procure from",
    "sales to",
    "sold to",
    "agreement with",
    "contract with",
    "sourced from",
    "rely on",
    "depend on",
)


def discover_cross_links(
    *,
    documents: list[SourceDocument],
    evidence_items: list[ParsedEvidence],
) -> list[ParsedEvidence]:
    known_entities = collect_known_entities(evidence_items)
    if not known_entities:
        return []

    discoveries: list[ParsedEvidence] = []
    seen_ids = {item.evidence_id for item in evidence_items}
    existing_relationship_keys = {
        (
            normalize_name(item.reporter_name),
            normalize_name(item.counterparty_name),
            item.relation_type.value,
            item.document_id,
        )
        for item in evidence_items
        if item.named_counterparty
    }
    for document in documents:
        reporter_key = normalize_name(document.company_name)
        text = extract_document_text(document)
        for sentence in split_sentences(text):
            lowered = sentence.lower()
            if not any(keyword in lowered for keyword in SUPPLY_CONTEXT_KEYWORDS):
                continue
            relation_type = infer_relation_type(lowered)
            for entity_name in known_entities:
                candidate_key = normalize_name(entity_name)
                if candidate_key == reporter_key or candidate_key in reporter_key or reporter_key in candidate_key:
                    continue
                if not entity_name_in_sentence(entity_name, sentence):
                    continue
                relationship_key = (
                    reporter_key,
                    candidate_key,
                    relation_type.value,
                    document.document_id,
                )
                if relationship_key in existing_relationship_keys:
                    continue
                evidence = ParsedEvidence(
                    evidence_id=_make_evidence_id(document.document_id, f"{entity_name}:{sentence[:200]}"),
                    country=document.country,
                    relation_type=relation_type,
                    reporter_name=document.company_name,
                    counterparty_name=entity_name,
                    confidence=ConfidenceBand.MEDIUM,
                    source_system=document.source_system,
                    document_id=document.document_id,
                    document_title=document.title,
                    excerpt=sentence[:500],
                    filing_year=document.filing_year,
                    parser_method="cross_document_known_entity_probe",
                    download_url=document.download_url,
                    local_path=document.local_path,
                )
                if evidence.evidence_id not in seen_ids:
                    discoveries.append(evidence)
                    seen_ids.add(evidence.evidence_id)
                    existing_relationship_keys.add(relationship_key)
    return discoveries


def collect_known_entities(evidence_items: list[ParsedEvidence]) -> list[str]:
    names: list[str] = []
    for item in evidence_items:
        if item.named_counterparty and _sufficiently_specific(item.counterparty_name):
            if item.counterparty_name not in names:
                names.append(item.counterparty_name)
    return names


def extract_document_text(document: SourceDocument) -> str:
    if document.local_path.endswith(".pdf"):
        return extract_text_from_pdf(document.local_path, max_pages=80)
    return _html_to_text(Path(document.local_path).read_text(errors="ignore"))


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text)
    return [segment.strip() for segment in re.split(r"(?<=[\.;])\s+", normalized) if segment.strip()]


def infer_relation_type(sentence: str) -> RelationType:
    if "customer" in sentence or "sales to" in sentence or "sold to" in sentence:
        return RelationType.CUSTOMER
    return RelationType.SUPPLIER


def entity_name_in_sentence(entity_name: str, sentence: str) -> bool:
    if any("\u4e00" <= char <= "\u9fff" for char in entity_name):
        return entity_name in sentence
    pattern = re.compile(rf"\b{re.escape(entity_name)}\b", re.I)
    return bool(pattern.search(sentence))


def _html_to_text(value: str) -> str:
    without_scripts = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    without_styles = re.sub(r"<style.*?</style>", " ", without_scripts, flags=re.S | re.I)
    without_tags = re.sub(r"<[^>]+>", " ", without_styles)
    return re.sub(r"\s+", " ", without_tags)


def _sufficiently_specific(name: str) -> bool:
    normalized = normalize_name(name)
    return len(normalized) >= 4 and "undisclosed" not in normalized


def _make_evidence_id(document_id: str, payload: str) -> str:
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:10]
    return f"{document_id}-ev-{digest}"
