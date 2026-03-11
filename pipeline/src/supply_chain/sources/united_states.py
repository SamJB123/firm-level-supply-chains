from __future__ import annotations

import json
import re

import requests

from supply_chain.config import REQUEST_HEADERS, get_config
from supply_chain.models import CompanySeed, Country, SourceDocument


TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/{cik}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_numeric}/{accession}/{document_name}"


def _safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fetch_ticker_map() -> dict[str, dict[str, str]]:
    response = requests.get(TICKER_MAP_URL, headers=REQUEST_HEADERS["sec"], timeout=30)
    response.raise_for_status()
    payload = response.json()
    mapping: dict[str, dict[str, str]] = {}
    for record in payload.values():
        ticker = str(record["ticker"]).upper()
        mapping[ticker] = {
            "cik": f"CIK{int(record['cik_str']):010d}",
            "title": str(record["title"]),
        }
    return mapping


def fetch_documents(seeds: list[CompanySeed], years_back: int = 3) -> list[SourceDocument]:
    config = get_config()
    ticker_map = fetch_ticker_map()
    documents: list[SourceDocument] = []

    for seed in seeds:
        ticker = seed.ticker.split(".")[0].upper()
        ticker_info = ticker_map.get(ticker)
        if not ticker_info:
            continue
        cik = ticker_info["cik"]
        submissions = requests.get(
            SUBMISSIONS_URL.format(cik=cik),
            headers=REQUEST_HEADERS["sec"],
            timeout=30,
        )
        submissions.raise_for_status()
        payload = submissions.json()

        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])
        filing_dates = recent.get("filingDate", [])

        local_dir = config.raw_dir / "us" / _safe_slug(seed.name)
        local_dir.mkdir(parents=True, exist_ok=True)

        downloaded_years: set[int] = set()
        for form, accession, primary_document, filing_date in zip(forms, accession_numbers, primary_documents, filing_dates, strict=False):
            if form not in {"10-K", "20-F"}:
                continue
            filing_year = int(str(filing_date)[:4])
            if filing_year in downloaded_years:
                continue
            if len(downloaded_years) >= years_back:
                break
            downloaded_years.add(filing_year)

            accession_compact = str(accession).replace("-", "")
            cik_numeric = int(cik.replace("CIK", ""))
            download_url = ARCHIVE_URL.format(
                cik_numeric=cik_numeric,
                accession=accession_compact,
                document_name=primary_document,
            )
            local_path = local_dir / f"{filing_year}-{form.lower()}.html"
            metadata_path = local_dir / f"{filing_year}-{form.lower()}.json"
            document_response = requests.get(
                download_url,
                headers=REQUEST_HEADERS["sec"],
                timeout=60,
            )
            document_response.raise_for_status()
            local_path.write_text(document_response.text)
            metadata_path.write_text(
                json.dumps(
                    {
                        "cik": cik,
                        "ticker": ticker,
                        "filing_date": filing_date,
                        "form": form,
                    },
                    indent=2,
                )
            )
            documents.append(
                SourceDocument(
                    document_id=f"us-{_safe_slug(seed.name)}-{filing_year}",
                    country=Country.UNITED_STATES,
                    company_name=seed.name,
                    source_system="SEC EDGAR",
                    document_type=form.lower(),
                    title=f"{seed.name} {form} {filing_year}",
                    filing_year=filing_year,
                    filing_date=str(filing_date),
                    download_url=download_url,
                    local_path=str(local_path),
                    metadata_path=str(metadata_path),
                )
            )

    return documents
