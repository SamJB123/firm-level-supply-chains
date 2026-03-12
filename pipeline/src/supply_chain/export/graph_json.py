from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from supply_chain.config import SOURCE_MANIFEST
from supply_chain.models import GraphBundle, GraphEdge, GraphNode, NormalizedEntity, NormalizedEdge, ParsedEvidence


def write_graph_bundle(
    *,
    entities: list[NormalizedEntity],
    edges: list[NormalizedEdge],
    evidence: list[ParsedEvidence],
    candidates,
    graph_path: str | Path,
    summary_path: str | Path,
) -> None:
    bundle = GraphBundle(
        nodes=[
            GraphNode(
                id=entity.entity_id,
                label=entity.display_name,
                country=entity.country,
                node_kind=entity.node_kind,
                aliases=entity.aliases,
                source_ids=entity.source_ids,
            )
            for entity in entities
        ],
        edges=[
            GraphEdge(
                id=edge.edge_id,
                source=edge.source_entity_id,
                target=edge.target_entity_id,
                relation_type=edge.relation_type,
                confidence=edge.confidence,
                explicit=edge.explicit,
                evidence_ids=edge.evidence_ids,
            )
            for edge in edges
        ],
        evidence=evidence,
        candidates=candidates,
        sources=SOURCE_MANIFEST,
    )
    Path(graph_path).write_text(bundle.model_dump_json(indent=2))
    Path(summary_path).write_text(
        json.dumps(
            {
                "nodeCount": len(bundle.nodes),
                "edgeCount": len(bundle.edges),
                "evidenceCount": len(bundle.evidence),
                "candidateCount": len(bundle.candidates),
                "explicitEdgeCount": len([edge for edge in bundle.edges if edge.explicit]),
                "placeholderEdgeCount": len([edge for edge in bundle.edges if not edge.explicit]),
                "sources": SOURCE_MANIFEST,
                "countries": sorted({node.country.value for node in bundle.nodes}),
            },
            indent=2,
        )
    )


def publish_versioned_web_assets(
    *,
    graph_path: str | Path,
    summary_path: str | Path,
    web_public_dir: str | Path,
    web_generated_dir: str | Path,
) -> str:
    graph_file = Path(graph_path)
    summary_file = Path(summary_path)
    web_public = Path(web_public_dir)
    web_generated = Path(web_generated_dir)
    web_public.mkdir(parents=True, exist_ok=True)
    web_generated.mkdir(parents=True, exist_ok=True)

    graph_text = graph_file.read_text()
    summary_text = summary_file.read_text()
    version = hashlib.md5(f"{graph_text}\n{summary_text}".encode("utf-8")).hexdigest()[:12]

    versioned_graph_name = f"graph-{version}.json"
    versioned_summary_name = f"summary-{version}.json"
    shutil.copyfile(graph_file, web_public / "graph.json")
    shutil.copyfile(summary_file, web_public / "summary.json")
    shutil.copyfile(graph_file, web_public / versioned_graph_name)
    shutil.copyfile(summary_file, web_public / versioned_summary_name)

    (web_generated / "dataManifest.ts").write_text(
        "\n".join(
            [
                "export const dataManifest = {",
                f"  graphPath: '/data/{versioned_graph_name}',",
                f"  summaryPath: '/data/{versioned_summary_name}',",
                f"  version: '{version}',",
                "} as const",
                "",
            ]
        )
    )
    return version
