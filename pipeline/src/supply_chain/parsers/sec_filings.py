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

SUPPLIER_CONTEXT_PATTERNS = [
    re.compile(
        r"(?:utilize|use|purchase(?: memory)? from|engage with|engage|rely on|depend on).{0,120}?(?:such as|from)\s(?P<context>[^.]{0,420})",
        re.I,
    ),
    re.compile(
        r"(?:rely on|depend on)\s(?P<context>[^.]{0,220})\s(?:to manufacture|to supply|for manufacturing)",
        re.I,
    ),
    re.compile(
        r"(?:foundries|contract manufacturers|subcontractors|assembly partners).{0,80}?(?:such as|include)\s(?P<context>[^.]{0,420})",
        re.I,
    ),
]

CUSTOMER_CONTEXT_PATTERNS = [
    re.compile(
        r"(?:customers include|direct customers include).{0,20}(?P<context>[^.]{0,420})",
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
    reporter_name_key = normalize_name(document.company_name)

    for pattern in SUPPLIER_CONTEXT_PATTERNS:
        for match in pattern.finditer(normalized_text):
            for counterparty_name in _extract_company_names(match.group("context")):
                if _same_company_name(counterparty_name, reporter_name_key):
                    continue
                evidence.append(
                    ParsedEvidence(
                        evidence_id=_make_evidence_id(document.document_id, f"{match.group(0)}::{counterparty_name}"),
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

    for pattern in CUSTOMER_CONTEXT_PATTERNS:
        for match in pattern.finditer(normalized_text):
            for counterparty_name in _extract_company_names(match.group("context")):
                if _same_company_name(counterparty_name, reporter_name_key):
                    continue
                evidence.append(
                    ParsedEvidence(
                        evidence_id=_make_evidence_id(document.document_id, f"{match.group(0)}::{counterparty_name}"),
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
