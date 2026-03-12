from pathlib import Path

from supply_chain.models import ConfidenceBand, Country, ParsedEvidence, RelationType, SourceDocument
from supply_chain.normalize.interconnections import discover_cross_links


def test_discover_cross_links_finds_known_named_entity_in_other_document(tmp_path: Path):
    filing_path = tmp_path / "broadcom.html"
    filing_path.write_text(
        """
        <html><body>
        We outsource a majority of our manufacturing operations, including Taiwan Semiconductor Manufacturing Company Limited.
        </body></html>
        """
    )
    document = SourceDocument(
        document_id="us-broadcom-2025",
        country=Country.UNITED_STATES,
        company_name="Broadcom",
        source_system="SEC EDGAR",
        document_type="10-k",
        title="Broadcom 10-K 2025",
        filing_year=2025,
        download_url="https://example.com/broadcom.html",
        local_path=str(filing_path),
    )
    existing_evidence = [
        ParsedEvidence(
            evidence_id="ev-1",
            country=Country.UNITED_STATES,
            relation_type=RelationType.SUPPLIER,
            reporter_name="NVIDIA",
            counterparty_name="Taiwan Semiconductor Manufacturing Company Limited",
            confidence=ConfidenceBand.MEDIUM,
            source_system="SEC EDGAR",
            document_id="doc-1",
            document_title="NVIDIA 10-K",
            excerpt="NVIDIA relies on Taiwan Semiconductor Manufacturing Company Limited.",
            parser_method="sec_supplier_regex",
        )
    ]

    discovered = discover_cross_links(documents=[document], evidence_items=existing_evidence)

    assert len(discovered) == 1
    assert discovered[0].reporter_name == "Broadcom"
    assert discovered[0].counterparty_name == "Taiwan Semiconductor Manufacturing Company Limited"
