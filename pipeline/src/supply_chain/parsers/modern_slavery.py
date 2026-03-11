from __future__ import annotations

import hashlib
import re

from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType, SourceDocument
from supply_chain.parsers.pdf_text import extract_text_from_pdf


NAMED_RELATION_PATTERN = re.compile(
    r"(?P<counterparty>[A-Z][A-Za-z&.,'() -]{2,}(?:Ltd|Limited|Corp|Corporation|Inc|PLC|Group|Company|Co\.|LLC|Pty Ltd|Pty\. Ltd\.))"
    r".{0,80}?(?P<keyword>supplier|customer|partner|manufacturer|contractor)",
    re.I,
)

SUPPLY_CHAIN_KEYWORDS = (
    "supplier",
    "suppliers",
    "customer",
    "customers",
    "manufacturing partner",
    "contract manufacturer",
)


def parse_document(document: SourceDocument) -> list[ParsedEvidence]:
    text = extract_text_from_pdf(document.local_path, max_pages=25)
    normalized_text = re.sub(r"\s+", " ", text)
    evidence: list[ParsedEvidence] = []

    for match in NAMED_RELATION_PATTERN.finditer(normalized_text):
        keyword = match.group("keyword").lower()
        relation_type = RelationType.SUPPLIER if "supplier" in keyword or "manufacturer" in keyword or "contractor" in keyword else RelationType.CUSTOMER
        evidence.append(
            ParsedEvidence(
                evidence_id=_make_evidence_id(document.document_id, match.group(0)),
                country=Country.AUSTRALIA,
                relation_type=relation_type,
                reporter_name=document.company_name,
                counterparty_name=match.group("counterparty").strip(),
                confidence=ConfidenceBand.MEDIUM,
                source_system=document.source_system,
                document_id=document.document_id,
                document_title=document.title,
                excerpt=match.group(0).strip(),
                filing_year=document.filing_year,
                parser_method="modern_slavery_named_regex",
                download_url=document.download_url,
                local_path=document.local_path,
            )
        )

    if evidence:
        return evidence

    if any(keyword in normalized_text.lower() for keyword in SUPPLY_CHAIN_KEYWORDS):
        evidence.append(
            ParsedEvidence(
                evidence_id=_make_evidence_id(document.document_id, "undisclosed-supplier"),
                country=Country.AUSTRALIA,
                relation_type=RelationType.UNDISCLOSED_SUPPLIER,
                reporter_name=document.company_name,
                counterparty_name="Undisclosed Supplier",
                confidence=ConfidenceBand.LOW,
                source_system=document.source_system,
                document_id=document.document_id,
                document_title=document.title,
                excerpt=normalized_text[:500],
                filing_year=document.filing_year,
                parser_method="modern_slavery_placeholder",
                named_counterparty=False,
                download_url=document.download_url,
                local_path=document.local_path,
            )
        )

    return evidence


def _make_evidence_id(document_id: str, payload: str) -> str:
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:10]
    return f"{document_id}-ev-{digest}"
