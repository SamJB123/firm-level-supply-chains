from __future__ import annotations

import hashlib
import re

from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType, SourceDocument
from supply_chain.parsers.pdf_text import extract_text_from_pdf


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
