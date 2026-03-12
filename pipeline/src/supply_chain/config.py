from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
PROCESSED_DIR = DATA_DIR / "processed"
DEMO_DIR = PROCESSED_DIR / "demo"
CONFIG_DIR = ROOT_DIR / "config"
WEB_PUBLIC_DIR = ROOT_DIR / "apps" / "web" / "public" / "data"
WEB_GENERATED_DIR = ROOT_DIR / "apps" / "web" / "src" / "lib" / "generated"


SOURCE_MANIFEST = {
    "AU": [
        "Modern Slavery Statements Register",
        "Public annual report / announcement PDFs",
        "ABN Lookup / Australian Business Register",
    ],
    "CN": [
        "CNINFO announcement metadata",
        "CNINFO annual and semiannual report PDFs",
    ],
    "US": [
        "SEC EDGAR submissions metadata",
        "SEC filing HTML / exhibits",
        "SEC XBRL and CompanyFacts APIs",
    ],
}


REQUEST_HEADERS = {
    "generic": {"User-Agent": "SupplyChainLinksResearch/0.1 contact@example.com"},
    "browser": {"User-Agent": "Mozilla/5.0"},
    "sec": {"User-Agent": "SupplyChainLinksResearch/0.1 contact@example.com"},
    "cninfo": {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
    },
}


@dataclass(frozen=True)
class AppConfig:
    root_dir: Path = ROOT_DIR
    data_dir: Path = DATA_DIR
    raw_dir: Path = RAW_DIR
    intermediate_dir: Path = INTERMEDIATE_DIR
    processed_dir: Path = PROCESSED_DIR
    demo_dir: Path = DEMO_DIR
    config_dir: Path = CONFIG_DIR
    web_public_dir: Path = WEB_PUBLIC_DIR
    web_generated_dir: Path = WEB_GENERATED_DIR

    def ensure_directories(self) -> None:
        for path in [
            self.raw_dir / "au",
            self.raw_dir / "cn",
            self.raw_dir / "us",
            self.intermediate_dir / "au",
            self.intermediate_dir / "cn",
            self.intermediate_dir / "us",
            self.demo_dir,
            self.web_public_dir,
            self.web_generated_dir,
            self.config_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


def get_config() -> AppConfig:
    config = AppConfig()
    config.ensure_directories()
    return config
