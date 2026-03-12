from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

from supply_chain.config import get_config
from supply_chain.export.graph_json import write_graph_bundle
from supply_chain.export.tables import write_tables
from supply_chain.models import CompanySeed, Country, ParsedEvidence, SourceDocument
from supply_chain.normalize.edges import build_edges
from supply_chain.normalize.entities import build_entities, load_overrides, normalize_name
from supply_chain.normalize.evidence import rescore_evidence
from supply_chain.parsers.cn_suppliers_customers import parse_document as parse_cn_document
from supply_chain.parsers.modern_slavery import parse_document as parse_au_document
from supply_chain.parsers.sec_filings import parse_document as parse_us_document
from supply_chain.sources.australia import fetch_documents as fetch_au_documents
from supply_chain.sources.china import fetch_documents as fetch_cn_documents
from supply_chain.sources.market_cap import fetch_all_top_companies
from supply_chain.sources.united_states import fetch_documents as fetch_us_documents

def main() -> None:
    parser = argparse.ArgumentParser(description="Supply chain data pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate-seeds", help="Generate top market-cap seed universe")
    generate_parser.add_argument("--limit", type=int, default=20)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch country documents for selected seeds")
    fetch_parser.add_argument("--country", choices=["AU", "CN", "US"], required=True)
    fetch_parser.add_argument("--limit", type=int, default=3)
    fetch_parser.add_argument("--selector", default="")
    fetch_parser.add_argument("--years-back", type=int, default=3)

    build_demo_parser = subparsers.add_parser("build-demo", help="Build demo graph from downloaded real sources")
    build_demo_parser.add_argument("--seed-limit", type=int, default=20)
    build_demo_parser.add_argument("--country-limit", type=int, default=20)
    build_demo_parser.add_argument("--years-back", type=int, default=3)

    args = parser.parse_args()
    if args.command == "generate-seeds":
        generate_seeds(limit=args.limit)
    elif args.command == "fetch":
        fetch(country=Country(args.country), limit=args.limit, selector=args.selector, years_back=args.years_back)
    elif args.command == "build-demo":
        build_demo(seed_limit=args.seed_limit, country_limit=args.country_limit, years_back=args.years_back)


def generate_seeds(limit: int = 20) -> Path:
    config = get_config()
    seeds = list(fetch_all_top_companies(limit=limit))
    output_path = config.config_dir / "seed_companies.csv"
    with output_path.open("w", newline="") as handle:
        fieldnames = list(CompanySeed.model_fields.keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for seed in seeds:
            writer.writerow(seed.model_dump())
    overrides_path = config.config_dir / "entity_overrides.csv"
    if not overrides_path.exists():
        overrides_path.write_text("raw_name,canonical_name\n")
    print(f"Wrote {len(seeds)} seeds to {output_path}")
    return output_path


def fetch(country: Country, limit: int, selector: str, years_back: int) -> Path:
    seeds = load_seeds()
    selected_seeds = select_seeds(seeds=seeds, country=country, selector=selector, limit=limit)
    documents = _fetch_for_country(country=country, seeds=selected_seeds, years_back=years_back)
    config = get_config()
    manifest_path = config.intermediate_dir / country.value.lower() / "document_manifest.json"
    manifest_path.write_text(json.dumps([document.model_dump() for document in documents], indent=2, ensure_ascii=False))
    print(f"Fetched {len(documents)} documents for {country.value} into {manifest_path}")
    return manifest_path


def build_demo(seed_limit: int = 20, country_limit: int = 20, years_back: int = 3) -> None:
    config = get_config()
    if not (config.config_dir / "seed_companies.csv").exists():
        generate_seeds(limit=seed_limit)

    seeds = load_seeds()
    documents: list[SourceDocument] = []
    for country in [Country.AUSTRALIA, Country.CHINA, Country.UNITED_STATES]:
        documents.extend(
            _fetch_for_country(
                country=country,
                seeds=select_build_seeds(seeds, country, country_limit=country_limit),
                years_back=years_back,
            )
        )

    evidence = parse_documents(documents)
    evidence = rescore_evidence(evidence)
    overrides = load_overrides(config.config_dir / "entity_overrides.csv")
    entities, entity_lookup = build_entities(evidence, overrides)
    edges, candidates = build_edges(evidence, entity_lookup)

    write_tables(
        entities=entities,
        edges=edges,
        evidence=evidence,
        candidates=candidates,
        output_dir=config.demo_dir,
    )
    write_graph_bundle(
        entities=entities,
        edges=edges,
        evidence=evidence,
        candidates=candidates,
        graph_path=config.demo_dir / "graph.json",
        summary_path=config.demo_dir / "summary.json",
    )
    shutil.copyfile(config.demo_dir / "graph.json", config.web_public_dir / "graph.json")
    shutil.copyfile(config.demo_dir / "summary.json", config.web_public_dir / "summary.json")
    print(f"Built demo graph with {len(entities)} nodes, {len(edges)} edges, and {len(candidates)} candidates.")


def load_seeds() -> list[CompanySeed]:
    config = get_config()
    path = config.config_dir / "seed_companies.csv"
    if not path.exists():
        raise FileNotFoundError("seed_companies.csv not found. Run generate-seeds first.")
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return [CompanySeed(**row) for row in reader]


def select_seeds(seeds: list[CompanySeed], country: Country, selector: str, limit: int) -> list[CompanySeed]:
    country_seeds = [seed for seed in seeds if seed.country == country]
    if selector:
        wanted = [name.strip().lower() for name in selector.split(",") if name.strip()]
        selected = [
            seed
            for seed in country_seeds
            if any(token in seed.name.lower() or token in seed.ticker.lower() for token in wanted)
        ]
        return selected[:limit]
    return country_seeds[:limit]


def select_demo_seeds(seeds: list[CompanySeed], country: Country) -> list[CompanySeed]:
    return select_build_seeds(seeds, country, country_limit=3)


def select_build_seeds(seeds: list[CompanySeed], country: Country, country_limit: int) -> list[CompanySeed]:
    country_seeds = [seed for seed in seeds if seed.country == country]
    return country_seeds[:country_limit]


def parse_documents(documents: list[SourceDocument]) -> list[ParsedEvidence]:
    evidence: list[ParsedEvidence] = []
    for document in documents:
        if "SEC EDGAR" in document.source_system:
            evidence.extend(parse_us_document(document))
        elif document.country == Country.AUSTRALIA:
            evidence.extend(parse_au_document(document))
        elif document.country == Country.CHINA:
            evidence.extend(parse_cn_document(document))
    return evidence


def _fetch_for_country(country: Country, seeds: list[CompanySeed], years_back: int) -> list[SourceDocument]:
    if country == Country.AUSTRALIA:
        return fetch_au_documents(seeds=seeds, limit_per_company=min(years_back, 2))
    if country == Country.CHINA:
        return fetch_cn_documents(seeds=seeds, years_back=years_back)
    if country == Country.UNITED_STATES:
        return fetch_us_documents(seeds=seeds, years_back=years_back)
    return []


if __name__ == "__main__":
    main()
