import json
from pathlib import Path

from supply_chain.export.graph_json import write_graph_bundle
from supply_chain.models import (
    CandidateLink,
    ConfidenceBand,
    Country,
    NormalizedEdge,
    NormalizedEntity,
    ParsedEvidence,
    RelationType,
)


def test_graph_export_writes_summary_and_bundle(tmp_path: Path):
    graph_path = tmp_path / "graph.json"
    summary_path = tmp_path / "summary.json"
    write_graph_bundle(
        entities=[
            NormalizedEntity(entity_id="ent-1", display_name="SupplierCo", country=Country.UNITED_STATES),
            NormalizedEntity(entity_id="ent-2", display_name="CustomerCo", country=Country.CHINA),
        ],
        edges=[
            NormalizedEdge(
                edge_id="edge-1",
                source_entity_id="ent-1",
                target_entity_id="ent-2",
                relation_type=RelationType.SUPPLIER,
                confidence=ConfidenceBand.MEDIUM,
                evidence_ids=["ev-1"],
                countries=[Country.UNITED_STATES],
                source_systems=["SEC EDGAR"],
            )
        ],
        evidence=[
            ParsedEvidence(
                evidence_id="ev-1",
                country=Country.UNITED_STATES,
                relation_type=RelationType.SUPPLIER,
                reporter_name="CustomerCo",
                counterparty_name="SupplierCo",
                confidence=ConfidenceBand.MEDIUM,
                source_system="SEC EDGAR",
                document_id="doc-1",
                document_title="10-K",
                excerpt="excerpt",
                parser_method="sec_supplier_regex",
            )
        ],
        candidates=[
            CandidateLink(
                candidate_link_id="cand-1",
                undisclosed_entity_id="ent-3",
                candidate_entity_id="ent-1",
                rank=1,
                confidence=ConfidenceBand.LOW,
                rationale="Other evidence points to SupplierCo",
                supporting_evidence_ids=["ev-1"],
            )
        ],
        graph_path=graph_path,
        summary_path=summary_path,
    )

    summary = json.loads(summary_path.read_text())
    assert graph_path.exists()
    assert summary["nodeCount"] == 2
    assert summary["candidateCount"] == 1
