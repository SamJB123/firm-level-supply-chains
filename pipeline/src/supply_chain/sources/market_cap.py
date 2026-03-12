from __future__ import annotations

import re
from typing import Iterable

import requests

from supply_chain.config import REQUEST_HEADERS
from supply_chain.models import CompanySeed, Country


COUNTRY_PAGES: dict[Country, str] = {
    Country.AUSTRALIA: "https://www.companiesmarketcap.com/australia/largest-companies-in-australia-by-market-cap/",
    Country.CHINA: "https://www.companiesmarketcap.com/china/largest-companies-in-china-by-market-cap/",
    Country.UNITED_STATES: "https://www.companiesmarketcap.com/usa/largest-companies-in-the-usa-by-market-cap/",
}


ROW_PATTERN = re.compile(
    r'<tr><td class="fav".*?<td class="rank-td td-right" data-sort="(?P<rank>\d+)">.*?'
    r'<a href="/(?P<slug>[^/]+)/marketcap/">'
    r'<div class="company-name">(?P<name>.*?)</div>'
    r'<div class="company-code"><span class="rank d-none"></span>(?P<ticker>.*?)</div>'
    r".*?<td class=\"td-right\" data-sort=\"(?P<market_cap>\d+)\">",
    re.S,
)

EASTMONEY_NAME_URL = "https://push2.eastmoney.com/api/qt/stock/get"
CNINFO_SEARCH_NAME_OVERRIDES = {
    "中国建设银行": "建设银行",
    "中国农业银行": "农业银行",
}


def _clean_html_text(value: str) -> str:
    return re.sub(r"<.*?>", "", value).strip()


def _lookup_chinese_search_name(ticker: str, exchange: str) -> str:
    ticker_code = ticker.split(".")[0].upper()
    if exchange == "SS":
        secid = f"1.{ticker_code}"
    elif exchange == "SZ":
        secid = f"0.{ticker_code}"
    elif exchange == "HK":
        secid = f"116.{ticker_code.zfill(5)}"
    else:
        return ""

    response = requests.get(
        EASTMONEY_NAME_URL,
        headers={
            **REQUEST_HEADERS["browser"],
            "Referer": "https://quote.eastmoney.com/",
        },
        params={"secid": secid, "fields": "f57,f58"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or {}
    name = str(data.get("f58", "")).strip()
    if not name:
        return ""
    return CNINFO_SEARCH_NAME_OVERRIDES.get(name, name)


def fetch_top_companies(country: Country, limit: int = 20) -> list[CompanySeed]:
    response = requests.get(
        COUNTRY_PAGES[country],
        headers=REQUEST_HEADERS["browser"],
        timeout=30,
    )
    response.raise_for_status()

    seeds: list[CompanySeed] = []
    for match in ROW_PATTERN.finditer(response.text):
        if len(seeds) >= limit:
            break
        name = _clean_html_text(match.group("name"))
        ticker = _clean_html_text(match.group("ticker"))
        slug = match.group("slug")
        market_cap_billions = round(int(match.group("market_cap")) / 1_000_000_000, 2)
        profile_url = f"https://www.companiesmarketcap.com/{slug}/marketcap/"
        seeds.append(
            CompanySeed(
                country=country,
                rank=int(match.group("rank")),
                name=name,
                ticker=ticker,
                exchange=ticker.split(".")[-1] if "." in ticker else "",
                market_cap_usd_billions=market_cap_billions,
                source_url=COUNTRY_PAGES[country],
                profile_url=profile_url,
                statement_search_name=(
                    _lookup_chinese_search_name(ticker=ticker, exchange=ticker.split(".")[-1] if "." in ticker else "")
                    if country == Country.CHINA
                    else name
                ),
            )
        )
    return seeds


def fetch_all_top_companies(limit: int = 20) -> Iterable[CompanySeed]:
    for country in [
        Country.AUSTRALIA,
        Country.CHINA,
        Country.UNITED_STATES,
    ]:
        yield from fetch_top_companies(country=country, limit=limit)
