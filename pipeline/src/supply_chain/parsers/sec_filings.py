from __future__ import annotations

import hashlib
import re
from html import unescape
from pathlib import Path

from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType, SourceDocument


SUPPLIER_PATTERNS = [
    re.compile(
        r"(?P<counterparty>[A-Z][A-Za-z0-9&.,'() -]{2,}(?:Inc\.|Inc|Corporation|Corp\.|Corp|Ltd\.|Ltd|Limited|Company|Co\.|LLC|Group|Technologies|Technology|Semiconductor|Electronics))"
        r".{0,120}?(?:manufactur|supply|foundry|assembly|fabricat)",
        re.I,
    ),
    re.compile(
        r"(?:depend on|rely on|purchase from|sourced from).{0,80}?(?P<counterparty>[A-Z][A-Za-z0-9&.,'() -]{2,}(?:Inc\.|Inc|Corporation|Corp\.|Corp|Ltd\.|Ltd|Limited|Company|Co\.|LLC|Group|Technologies|Technology|Semiconductor|Electronics))",
        re.I,
    ),
]

CUSTOMER_PATTERNS = [
    re.compile(
        r"(?P<counterparty>[A-Z][A-Za-z0-9&.,'() -]{2,}(?:Inc\.|Inc|Corporation|Corp\.|Corp|Ltd\.|Ltd|Limited|Company|Co\.|LLC|Group|Technologies|Technology))"
        r".{0,80}?(?:customer|customers)",
        re.I,
    )
]

UNDISCLOSED_PATTERN = re.compile(
    r"(?:single customer|one customer|major customer|largest customer).{0,120}?(?:10%|ten percent|significant portion)",
    re.I,
)


def parse_document(document: SourceDocument) -> list[ParsedEvidence]:
    text = Path(document.local_path).read_text(errors="ignore")
    normalized_text = _html_to_text(text)
    evidence: list[ParsedEvidence] = []

    for pattern in SUPPLIER_PATTERNS:
        for match in pattern.finditer(normalized_text):
            counterparty_name = match.group("counterparty").strip()
            if counterparty_name == document.company_name:
                continue
            evidence.append(
                ParsedEvidence(
                    evidence_id=_make_evidence_id(document.document_id, match.group(0)),
                    country=Country.UNITED_STATES,
                    relation_type=RelationType.SUPPLIER,
                    reporter_name=document.company_name,
                    counterparty_name=counterparty_name,
                    confidence=ConfidenceBand.MEDIUM,
                    source_system=document.source_system,
                    document_id=document.document_id,
                    document_title=document.title,
                    excerpt=match.group(0).strip(),
                    filing_year=document.filing_year,
                    parser_method="sec_supplier_regex",
                    download_url=document.download_url,
                    local_path=document.local_path,
                )
            )

    for pattern in CUSTOMER_PATTERNS:
        for match in pattern.finditer(normalized_text):
            counterparty_name = match.group("counterparty").strip()
            if counterparty_name == document.company_name:
                continue
            evidence.append(
                ParsedEvidence(
                    evidence_id=_make_evidence_id(document.document_id, match.group(0)),
                    country=Country.UNITED_STATES,
                    relation_type=RelationType.CUSTOMER,
                    reporter_name=document.company_name,
                    counterparty_name=counterparty_name,
                    confidence=ConfidenceBand.LOW,
                    source_system=document.source_system,
                    document_id=document.document_id,
                    document_title=document.title,
                    excerpt=match.group(0).strip(),
                    filing_year=document.filing_year,
                    parser_method="sec_customer_regex",
                    download_url=document.download_url,
                    local_path=document.local_path,
                )
            )

    if not evidence:
        for match in UNDISCLOSED_PATTERN.finditer(normalized_text):
            evidence.append(
                ParsedEvidence(
                    evidence_id=_make_evidence_id(document.document_id, match.group(0)),
                    country=Country.UNITED_STATES,
                    relation_type=RelationType.UNDISCLOSED_CUSTOMER,
                    reporter_name=document.company_name,
                    counterparty_name="Undisclosed Customer",
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


def _make_evidence_id(document_id: str, payload: str) -> str:
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:10]
    return f"{document_id}-ev-{digest}"
