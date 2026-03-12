from supply_chain.models import ConfidenceBand, Country, RelationType, SourceDocument
from supply_chain.parsers import modern_slavery


def test_modern_slavery_parser_creates_placeholder_when_no_named_counterparty(monkeypatch):
    monkeypatch.setattr(
        modern_slavery,
        "extract_text_from_pdf",
        lambda *args, **kwargs: "Our suppliers are central to our supply chain due diligence program.",
    )
    document = SourceDocument(
        document_id="au-test-1",
        country=Country.AUSTRALIA,
        company_name="BHP Group",
        source_system="Modern Slavery Statements Register",
        document_type="modern_slavery_statement",
        title="Statement #2025-1916",
        filing_year=2025,
        download_url="https://example.com/statement.pdf",
        local_path="/tmp/statement.pdf",
    )

    evidence = modern_slavery.parse_document(document)

    assert len(evidence) == 1
    assert evidence[0].relation_type == RelationType.UNDISCLOSED_SUPPLIER
    assert evidence[0].confidence == ConfidenceBand.LOW
    assert evidence[0].named_counterparty is False
