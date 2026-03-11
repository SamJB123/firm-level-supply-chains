from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType
from supply_chain.normalize.entities import build_entities


def test_entity_resolution_applies_overrides():
    evidence = [
        ParsedEvidence(
            evidence_id="ev-1",
            country=Country.UNITED_STATES,
            relation_type=RelationType.SUPPLIER,
            reporter_name="NVIDIA Corporation",
            counterparty_name="Taiwan Semiconductor Manufacturing Company Limited",
            confidence=ConfidenceBand.MEDIUM,
            source_system="SEC EDGAR",
            document_id="doc-1",
            document_title="10-K",
            excerpt="excerpt",
            parser_method="sec_supplier_regex",
        )
    ]

    entities, lookup = build_entities(evidence, {"taiwan semiconductor manufacturing": "TSMC"})

    labels = {entity.display_name for entity in entities}
    assert "TSMC" in labels
    assert "nvidia" in "".join(lookup.keys())
