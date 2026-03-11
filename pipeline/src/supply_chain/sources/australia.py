from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote_plus, urljoin

import requests

from supply_chain.config import REQUEST_HEADERS, get_config
from supply_chain.models import CompanySeed, Country, SourceDocument


BASE_URL = "https://modernslaveryregister.gov.au"
SEARCH_URL = f"{BASE_URL}/statements/"


STATEMENT_LINK_PATTERN = re.compile(r'href="(/statements/(?P<statement_id>\d+)/)"')
TITLE_PATTERN = re.compile(r"<title>(?P<title>[^<]+)</title>")
PDF_PATH_PATTERN = re.compile(r'href="(?P<pdf>/statements/[^"]+/pdf/)"')
YEAR_PATTERN = re.compile(r"(20\d{2})")


def _safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def search_statement_links(company_name: str, limit: int = 3) -> list[str]:
    response = requests.get(
        f"{SEARCH_URL}?q={quote_plus(company_name)}",
        headers=REQUEST_HEADERS["browser"],
        timeout=30,
    )
    response.raise_for_status()

    seen: list[str] = []
    for match in STATEMENT_LINK_PATTERN.finditer(response.text):
        statement_url = urljoin(BASE_URL, match.group(1))
        if statement_url not in seen:
            seen.append(statement_url)
        if len(seen) >= limit:
            break
    return seen


def fetch_statement_document(seed: CompanySeed, limit: int = 3) -> list[SourceDocument]:
    config = get_config()
    results: list[SourceDocument] = []
    for index, statement_url in enumerate(search_statement_links(seed.statement_search_name or seed.name, limit=limit), start=1):
        html = requests.get(
            statement_url,
            headers=REQUEST_HEADERS["browser"],
            timeout=30,
        )
        html.raise_for_status()
        title_match = TITLE_PATTERN.search(html.text)
        pdf_match = PDF_PATH_PATTERN.search(html.text)
        if not pdf_match:
            continue

        download_url = urljoin(BASE_URL, pdf_match.group("pdf"))
        year_match = YEAR_PATTERN.search(title_match.group("title") if title_match else "")
        filing_year = int(year_match.group(1)) if year_match else None
        company_slug = _safe_slug(seed.name)
        local_dir = config.raw_dir / "au" / company_slug
        local_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = local_dir / f"statement-{index}.pdf"
        metadata_path = local_dir / f"statement-{index}.json"
        pdf_response = requests.get(
            download_url,
            headers=REQUEST_HEADERS["browser"],
            timeout=60,
        )
        pdf_response.raise_for_status()
        pdf_path.write_bytes(pdf_response.content)
        metadata_path.write_text(
            json.dumps(
                {
                    "statement_url": statement_url,
                    "download_url": download_url,
                    "company_name": seed.name,
                },
                indent=2,
            )
        )
        results.append(
            SourceDocument(
                document_id=f"au-{company_slug}-statement-{index}",
                country=Country.AUSTRALIA,
                company_name=seed.name,
                source_system="Modern Slavery Statements Register",
                document_type="modern_slavery_statement",
                title=title_match.group("title").strip() if title_match else f"{seed.name} statement {index}",
                filing_year=filing_year,
                download_url=download_url,
                local_path=str(pdf_path),
                metadata_path=str(metadata_path),
            )
        )
    return results


def fetch_documents(seeds: list[CompanySeed], limit_per_company: int = 1) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for seed in seeds:
        documents.extend(fetch_statement_document(seed=seed, limit=limit_per_company))
    return documents
