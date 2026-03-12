from __future__ import annotations

import hashlib
import re

from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType, SourceDocument
from supply_chain.parsers.pdf_tables import extract_lines_near_markers, normalize_table_line
from supply_chain.parsers.pdf_text import extract_text_from_pdf


CUSTOMER_MARKERS = ["前五名客户", "前五名客戶", "主要客户"]
SUPPLIER_MARKERS = ["前五名供应商", "前五名供應商", "主要供应商"]
MASKED_COUNTERPARTY_PATTERN = re.compile(r"(客户|供应商)[一二三四五12345]")
PERCENTAGE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)%")
NAMED_ENTITY_PATTERN = re.compile(r"[\u4e00-\u9fffA-Za-z0-9（）()·&]{3,}(?:公司|集团|股份|有限|银行|大学|厂|矿业|能源)")
TABLE_ROW_PATTERN = re.compile(r"^\d+\s+")
ROW_RANK_PATTERN = re.compile(r"^(?P<rank>\d+)\s+")


def parse_document(document: SourceDocument) -> list[ParsedEvidence]:
    text = extract_text_from_pdf(document.local_path, max_pages=80)
    snippets = extract_lines_near_markers(text, CUSTOMER_MARKERS + SUPPLIER_MARKERS, window=20)
    evidence: list[ParsedEvidence] = []

    for snippet in snippets:
        lines = [normalize_table_line(line) for line in snippet.splitlines() if normalize_table_line(line)]
        relation_type: RelationType | None = None
        for line in lines:
            if any(marker in line for marker in CUSTOMER_MARKERS):
                relation_type = RelationType.CUSTOMER
                continue
            if any(marker in line for marker in SUPPLIER_MARKERS):
                relation_type = RelationType.SUPPLIER
                continue
            if relation_type is None:
                continue
            if not TABLE_ROW_PATTERN.match(line):
                continue
            named_match = NAMED_ENTITY_PATTERN.search(line)
            percentage_match = PERCENTAGE_PATTERN.search(line)
            if named_match:
                counterparty_name = named_match.group(0)
                if counterparty_name == document.company_name or "年度报告" in line:
                    continue
                evidence.append(
                    ParsedEvidence(
                        evidence_id=_make_evidence_id(document.document_id, line),
                        country=Country.CHINA,
                        relation_type=relation_type,
                        reporter_name=document.company_name,
                        counterparty_name=counterparty_name,
                        confidence=ConfidenceBand.HIGH,
                        source_system=document.source_system,
                        document_id=document.document_id,
                        document_title=document.title,
                        excerpt=line,
                        percentage_text=percentage_match.group(0) if percentage_match else "",
                        filing_year=document.filing_year,
                        parser_method="cn_table_named_line",
                        download_url=document.download_url,
                        local_path=document.local_path,
                    )
                )
                continue

            if MASKED_COUNTERPARTY_PATTERN.search(line):
                row_rank_match = ROW_RANK_PATTERN.match(line)
                row_rank = row_rank_match.group("rank") if row_rank_match else "?"
                masked_name = (
                    f"Undisclosed Customer · {document.company_name} · {document.filing_year or document.document_id} · #{row_rank}"
                    if relation_type == RelationType.CUSTOMER
                    else f"Undisclosed Supplier · {document.company_name} · {document.filing_year or document.document_id} · #{row_rank}"
                )
                evidence.append(
                    ParsedEvidence(
                        evidence_id=_make_evidence_id(document.document_id, line),
                        country=Country.CHINA,
                        relation_type=RelationType.UNDISCLOSED_CUSTOMER if relation_type == RelationType.CUSTOMER else RelationType.UNDISCLOSED_SUPPLIER,
                        reporter_name=document.company_name,
                        counterparty_name=masked_name,
                        confidence=ConfidenceBand.MEDIUM,
                        source_system=document.source_system,
                        document_id=document.document_id,
                        document_title=document.title,
                        excerpt=line,
                        percentage_text=percentage_match.group(0) if percentage_match else "",
                        filing_year=document.filing_year,
                        parser_method="cn_table_masked_line",
                        named_counterparty=False,
                        download_url=document.download_url,
                        local_path=document.local_path,
                    )
                )

    deduped: dict[str, ParsedEvidence] = {}
    for item in evidence:
        deduped[item.evidence_id] = item
    return list(deduped.values())


def _make_evidence_id(document_id: str, payload: str) -> str:
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:10]
    return f"{document_id}-ev-{digest}"
