from supply_chain.models import Country, RelationType, SourceDocument
from supply_chain.parsers import cn_suppliers_customers


def test_cn_parser_extracts_named_and_masked_counterparties(monkeypatch):
    monkeypatch.setattr(
        cn_suppliers_customers,
        "extract_text_from_pdf",
        lambda *args, **kwargs: "\n".join(
            [
                "前五名客户",
                "1 比亚迪股份有限公司 12.4%",
                "2 客户一 10.2%",
                "前五名供应商",
                "1 宁德时代新能源科技股份有限公司 8.8%",
                "2 供应商一 4.1%",
            ]
        ),
    )
    document = SourceDocument(
        document_id="cn-test-1",
        country=Country.CHINA,
        company_name="示例公司",
        source_system="CNINFO",
        document_type="annual_report",
        title="示例公司2024年年度报告",
        filing_year=2024,
        download_url="https://example.com/report.pdf",
        local_path="/tmp/report.pdf",
    )

    evidence = cn_suppliers_customers.parse_document(document)

    relation_types = {item.relation_type for item in evidence}
    assert RelationType.CUSTOMER in relation_types
    assert RelationType.SUPPLIER in relation_types
    assert any(item.named_counterparty is False for item in evidence)
