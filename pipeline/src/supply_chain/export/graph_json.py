from __future__ import annotations

import json
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
