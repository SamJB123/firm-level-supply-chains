from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from supply_chain.models import CandidateLink, NormalizedEdge, NormalizedEntity, ParsedEvidence


def write_tables(
    *,
    entities: list[NormalizedEntity],
    edges: list[NormalizedEdge],
    evidence: list[ParsedEvidence],
    candidates: list[CandidateLink],
    output_dir: str | Path,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    _write(output_path / "entities.csv", entities, NormalizedEntity)
    _write(output_path / "edges.csv", edges, NormalizedEdge)
    _write(output_path / "evidence.csv", evidence, ParsedEvidence)
    _write(output_path / "candidate_links.csv", candidates, CandidateLink)

    _write(output_path / "entities.parquet", entities, NormalizedEntity)
    _write(output_path / "edges.parquet", edges, NormalizedEdge)
    _write(output_path / "evidence.parquet", evidence, ParsedEvidence)
    _write(output_path / "candidate_links.parquet", candidates, CandidateLink)


def _write(path: Path, items: list[object], schema: type[object]) -> None:
    rows = [item.model_dump() for item in items]
    if rows:
        frame = pd.DataFrame(rows)
    else:
        columns = list(getattr(schema, "model_fields").keys())
        frame = pd.DataFrame(columns=columns)
    for column in frame.columns:
        frame[column] = frame[column].map(
            lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
        )
    if path.suffix == ".csv":
        frame.to_csv(path, index=False)
    else:
        frame.to_parquet(path, index=False)
