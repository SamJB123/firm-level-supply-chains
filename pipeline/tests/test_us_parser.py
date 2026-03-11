from pathlib import Path

from supply_chain.models import Country, RelationType, SourceDocument
from supply_chain.parsers.sec_filings import parse_document


def test_sec_parser_extracts_named_supplier(tmp_path: Path):
    filing_path = tmp_path / "filing.html"
    filing_path.write_text(
        """
        <html><body>
        We rely on Taiwan Semiconductor Manufacturing Company Limited to manufacture a substantial portion of our products.
        </body></html>
        """
    )
    document = SourceDocument(
        document_id="us-test-1",
        country=Country.UNITED_STATES,
        company_name="NVIDIA Corporation",
        source_system="SEC EDGAR",
        document_type="10-k",
        title="NVIDIA 10-K 2025",
        filing_year=2025,
        download_url="https://example.com/filing.html",
        local_path=str(filing_path),
    )

    evidence = parse_document(document)

    assert any(item.relation_type == RelationType.SUPPLIER for item in evidence)
    assert any("Taiwan Semiconductor" in item.counterparty_name for item in evidence)
