from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType
from supply_chain.normalize.edges import build_edges
from supply_chain.normalize.entities import build_entities


def test_candidate_inference_keeps_hypotheses_separate_from_explicit_edges():
    evidence = [
        ParsedEvidence(
            evidence_id="ev-1",
            country=Country.UNITED_STATES,
            relation_type=RelationType.CUSTOMER,
            reporter_name="SupplierCo",
            counterparty_name="ReporterCo",
            confidence=ConfidenceBand.MEDIUM,
            source_system="SEC EDGAR",
            document_id="doc-1",
            document_title="10-K",
            excerpt="SupplierCo's key customer is ReporterCo",
            parser_method="sec_customer_regex",
        ),
        ParsedEvidence(
            evidence_id="ev-2",
            country=Country.AUSTRALIA,
            relation_type=RelationType.UNDISCLOSED_SUPPLIER,
            reporter_name="ReporterCo",
            counterparty_name="Undisclosed Supplier",
            confidence=ConfidenceBand.LOW,
            source_system="Modern Slavery Statements Register",
            document_id="doc-2",
            document_title="Statement",
            excerpt="ReporterCo works with suppliers globally",
            parser_method="modern_slavery_placeholder",
            named_counterparty=False,
        ),
    ]

    entities, lookup = build_entities(evidence, {})
    edges, candidates = build_edges(evidence, lookup)

    assert any(edge.explicit is False for edge in edges)
    assert len(candidates) == 1
    assert candidates[0].supporting_evidence_ids == ["ev-1"]
