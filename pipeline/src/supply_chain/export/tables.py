from __future__ import annotations

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

    _write(output_path / "entities.csv", entities)
    _write(output_path / "edges.csv", edges)
    _write(output_path / "evidence.csv", evidence)
    _write(output_path / "candidate_links.csv", candidates)

    _write(output_path / "entities.parquet", entities)
    _write(output_path / "edges.parquet", edges)
    _write(output_path / "evidence.parquet", evidence)
    _write(output_path / "candidate_links.parquet", candidates)


def _write(path: Path, items: list[object]) -> None:
    frame = pd.DataFrame([item.model_dump() for item in items])
    if path.suffix == ".csv":
        frame.to_csv(path, index=False)
    else:
        frame.to_parquet(path, index=False)
