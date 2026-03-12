from __future__ import annotations

import hashlib
import re
from html import unescape
from pathlib import Path

from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType, SourceDocument
from supply_chain.normalize.entities import normalize_name


COMPANY_NAME_PATTERN = re.compile(
    r"(?:[A-Z][A-Za-z0-9&'().-]*\s){2,8}(?:Limited|Ltd\.|Ltd|Inc\.|Inc|Corporation|Corp\.|Corp|Company|Co\.|LLC|Group|Technologies|Technology|Semiconductor|Electronics)"
)

UNDISCLOSED_PATTERN = re.compile(
    r"(?:single customer|one customer|major customer|largest customer).{0,120}?(?:10%|ten percent|significant portion)",
    re.I,
)

SUPPLIER_CONTEXT_KEYWORDS = (
    "supplier",
    "suppliers",
    "rely on",
    "depend on",
    "foundries",
    "foundry",
    "assembly and test",
    "assembly",
    "testing",
    "packaging",
    "subcontractors",
    "contract manufacturers",
    "manufacturing operations",
    "battery cells",
    "wafer manufacturing",
    "procurement",
    "purchase materials from",
    "rely on suppliers",
    "depend on suppliers",
    "use third-party",
    "outsourced",
)

SUPPLIER_TRIGGER_KEYWORDS = (
    "such as",
    "including",
    "rely on",
    "depend on",
    "to manufacture",
    "to supply",
    "outsourced to",
    "we use",
    "we utilize",
    "we engage with",
)

SUPPLIER_NEGATIVE_KEYWORDS = (
    "compete",
    "competition",
    "competitors",
    "specific markets",
    "market share",
)

CUSTOMER_CONTEXT_KEYWORDS = (
    "customers include",
    "direct customers include",
    "customer represented",
    "major customer",
)


def parse_document(document: SourceDocument) -> list[ParsedEvidence]:
    text = Path(document.local_path).read_text(errors="ignore")
    normalized_text = _html_to_text(text)
    evidence: list[ParsedEvidence] = []
    reporter_name_key = normalize_name(document.company_name)

    for sentence in _split_sentences(normalized_text):
        lowered = sentence.lower()
        if _is_supplier_context(lowered):
            for counterparty_name in _extract_company_names(sentence):
                if _same_company_name(counterparty_name, reporter_name_key):
                    continue
                evidence.append(
                    ParsedEvidence(
                        evidence_id=_make_evidence_id(document.document_id, f"{sentence}::{counterparty_name}"),
                        country=Country.UNITED_STATES,
                        relation_type=RelationType.SUPPLIER,
                        reporter_name=document.company_name,
                        counterparty_name=counterparty_name,
                        confidence=ConfidenceBand.MEDIUM,
                        source_system=document.source_system,
                        document_id=document.document_id,
                        document_title=document.title,
                        excerpt=sentence.strip(),
                        filing_year=document.filing_year,
                        parser_method="sec_supplier_sentence_scan",
                        download_url=document.download_url,
                        local_path=document.local_path,
                    )
                )
        elif _is_customer_context(lowered):
            for counterparty_name in _extract_company_names(sentence):
                if _same_company_name(counterparty_name, reporter_name_key):
                    continue
                evidence.append(
                    ParsedEvidence(
                        evidence_id=_make_evidence_id(document.document_id, f"{sentence}::{counterparty_name}"),
                        country=Country.UNITED_STATES,
                        relation_type=RelationType.CUSTOMER,
                        reporter_name=document.company_name,
                        counterparty_name=counterparty_name,
                        confidence=ConfidenceBand.LOW,
                        source_system=document.source_system,
                        document_id=document.document_id,
                        document_title=document.title,
                        excerpt=sentence.strip(),
                        filing_year=document.filing_year,
                        parser_method="sec_customer_sentence_scan",
                        download_url=document.download_url,
                        local_path=document.local_path,
                    )
                )

    if not evidence:
        for match in UNDISCLOSED_PATTERN.finditer(normalized_text):
            placeholder_name = f"Undisclosed Customer · {document.company_name} · {document.document_id}"
            evidence.append(
                ParsedEvidence(
                    evidence_id=_make_evidence_id(document.document_id, match.group(0)),
                    country=Country.UNITED_STATES,
                    relation_type=RelationType.UNDISCLOSED_CUSTOMER,
                    reporter_name=document.company_name,
                    counterparty_name=placeholder_name,
                    confidence=ConfidenceBand.LOW,
                    source_system=document.source_system,
                    document_id=document.document_id,
                    document_title=document.title,
                    excerpt=match.group(0).strip(),
                    filing_year=document.filing_year,
                    parser_method="sec_undisclosed_customer_regex",
                    named_counterparty=False,
                    download_url=document.download_url,
                    local_path=document.local_path,
                )
            )

    deduped: dict[str, ParsedEvidence] = {}
    for item in evidence:
        deduped[item.evidence_id] = item
    return list(deduped.values())


def _html_to_text(value: str) -> str:
    without_scripts = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    without_styles = re.sub(r"<style.*?</style>", " ", without_scripts, flags=re.S | re.I)
    without_tags = re.sub(r"<[^>]+>", " ", without_styles)
    return re.sub(r"\s+", " ", unescape(without_tags))


def _split_sentences(value: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"(?<=[\.;])\s+", value) if segment.strip()]


def _is_supplier_context(sentence: str) -> bool:
    if any(keyword in sentence for keyword in SUPPLIER_NEGATIVE_KEYWORDS):
        return False
    return any(keyword in sentence for keyword in SUPPLIER_CONTEXT_KEYWORDS) and any(
        trigger in sentence for trigger in SUPPLIER_TRIGGER_KEYWORDS
    )


def _is_customer_context(sentence: str) -> bool:
    return any(keyword in sentence for keyword in CUSTOMER_CONTEXT_KEYWORDS)


def _extract_company_names(value: str) -> list[str]:
    cleaned_value = re.sub(r",\s+or\s+[A-Z0-9&'().-]+", "", value)
    found = [match.group(0).strip(" ,;") for match in COMPANY_NAME_PATTERN.finditer(cleaned_value)]
    deduped: list[str] = []
    for name in found:
        if _is_plausible_company_name(name) and name not in deduped:
            deduped.append(name)
    return deduped


def _is_plausible_company_name(value: str) -> bool:
    stripped = value.strip()
    if "Table of Contents" in stripped:
        return False
    if len(stripped.split()) < 3:
        return False
    if stripped.endswith(("technology", "technologies", "electronics", "semiconductor")):
        return False
    return True


def _make_evidence_id(document_id: str, payload: str) -> str:
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:10]
    return f"{document_id}-ev-{digest}"


def _same_company_name(candidate_name: str, reporter_name_key: str) -> bool:
    candidate_key = normalize_name(candidate_name)
    return candidate_key == reporter_name_key or candidate_key in reporter_name_key or reporter_name_key in candidate_key
