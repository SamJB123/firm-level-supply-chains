from __future__ import annotations

import json
import re

import requests

from supply_chain.config import REQUEST_HEADERS, get_config
from supply_chain.models import CompanySeed, Country, SourceDocument


QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
PDF_BASE_URL = "https://static.cninfo.com.cn/"
YEAR_PATTERN = re.compile(r"(20\d{2})年")


def _safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def query_annual_reports(company_name: str, page_size: int = 10) -> list[dict[str, object]]:
    response = requests.post(
        QUERY_URL,
        headers=REQUEST_HEADERS["cninfo"],
        data={
            "pageNum": "1",
            "pageSize": str(page_size),
            "tabName": "fulltext",
            "column": "szse",
            "stock": "",
            "plate": "",
            "searchkey": f"{company_name} 年度报告",
            "secid": "",
            "category": "category_ndbg_szsh",
            "trade": "",
            "seDate": "2023-01-01~2026-12-31",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("announcements") or []


def fetch_documents(seeds: list[CompanySeed], years_back: int = 3) -> list[SourceDocument]:
    config = get_config()
    documents: list[SourceDocument] = []
    for seed in seeds:
        company_slug = _safe_slug(seed.name)
        local_dir = config.raw_dir / "cn" / company_slug
        local_dir.mkdir(parents=True, exist_ok=True)

        seen_years: set[int] = set()
        for announcement in query_annual_reports(seed.name):
            title = str(announcement.get("announcementTitle", "")).replace("<em>", "").replace("</em>", "")
            if "摘要" in title:
                continue
            year_match = YEAR_PATTERN.search(title)
            if not year_match:
                continue
            filing_year = int(year_match.group(1))
            if filing_year in seen_years:
                continue
            if len(seen_years) >= years_back:
                break
            seen_years.add(filing_year)

            adjunct_url = str(announcement.get("adjunctUrl", ""))
            if not adjunct_url:
                continue
            download_url = f"{PDF_BASE_URL}{adjunct_url}"
            file_name = f"{filing_year}-annual-report.pdf"
            pdf_path = local_dir / file_name
            metadata_path = local_dir / f"{filing_year}-annual-report.json"
            if not pdf_path.exists():
                pdf_response = requests.get(
                    download_url,
                    headers=REQUEST_HEADERS["browser"],
                    timeout=90,
                )
                pdf_response.raise_for_status()
                pdf_path.write_bytes(pdf_response.content)
            if not metadata_path.exists():
                metadata_path.write_text(
                    json.dumps(
                        {
                            "seed_name": seed.name,
                            "query_name": seed.name,
                            "announcement": announcement,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            documents.append(
                SourceDocument(
                    document_id=f"cn-{company_slug}-{filing_year}",
                    country=Country.CHINA,
                    company_name=seed.name,
                    source_system="CNINFO",
                    document_type="annual_report",
                    title=title,
                    filing_year=filing_year,
                    download_url=download_url,
                    local_path=str(pdf_path),
                    metadata_path=str(metadata_path),
                )
            )
    return documents
