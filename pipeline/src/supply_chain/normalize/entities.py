from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

from supply_chain.models import Country, NormalizedEntity, ParsedEvidence


LEGAL_SUFFIXES = [
    "limited",
    "ltd",
    "inc",
    "corp",
    "corporation",
    "company",
    "co",
    "group",
    "pty ltd",
    "llc",
]


def normalize_name(value: str) -> str:
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", value.lower()).strip()
    for suffix in LEGAL_SUFFIXES:
        normalized = re.sub(rf"\b{re.escape(suffix)}\b", "", normalized).strip()
    return re.sub(r"\s+", " ", normalized).strip()


def load_overrides(path: str | Path) -> dict[str, str]:
    override_path = Path(path)
    if not override_path.exists():
        return {}
    overrides: dict[str, str] = {}
    with override_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_name = row.get("raw_name", "").strip()
            canonical_name = row.get("canonical_name", "").strip()
            if raw_name and canonical_name:
                overrides[normalize_name(raw_name)] = canonical_name
    return overrides


def build_entities(evidence_items: list[ParsedEvidence], overrides: dict[str, str]) -> tuple[list[NormalizedEntity], dict[str, str]]:
    entities: dict[str, NormalizedEntity] = {}
    name_to_entity_id: dict[str, str] = {}

    def ensure_entity(display_name: str, country: Country, node_kind: str = "company") -> str:
        override_name = overrides.get(normalize_name(display_name), display_name)
        canonical_key = normalize_name(override_name)
        if canonical_key in name_to_entity_id:
            return name_to_entity_id[canonical_key]
        entity_id = f"ent-{hashlib.md5(f'{country.value}:{canonical_key}'.encode('utf-8')).hexdigest()[:12]}"
        entity = NormalizedEntity(
            entity_id=entity_id,
            display_name=override_name,
            country=country,
            aliases=[display_name] if display_name != override_name else [],
            node_kind="placeholder" if node_kind == "placeholder" else "company",
        )
        entities[entity_id] = entity
        name_to_entity_id[canonical_key] = entity_id
        return entity_id

    for item in evidence_items:
        reporter_country = item.country if item.country != Country.OTHER else Country.OTHER
        ensure_entity(item.reporter_name, reporter_country)
        if item.counterparty_name:
            node_kind = "placeholder" if not item.named_counterparty else "company"
            country = item.counterparty_country or Country.OTHER
            ensure_entity(item.counterparty_name, country, node_kind=node_kind)

    return list(entities.values()), name_to_entity_id
