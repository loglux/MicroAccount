from __future__ import annotations

from app.documents.parse import (
    build_document_description,
    build_extracted_text_preview,
    parse_extracted_text,
)
from app.documents.schemas import DocumentExtractionResult


def test_parse_ionos_invoice_prefers_gross_amount_and_supplier() -> None:
    sample_text = """
    IONOS Cloud Ltd. No.2 Cathedral Walk
    Invoice No.: 203054576536
    Invoice Date: 08/04/2026
    Contract: 111511617 - IONOS VPS Linux L+
    Subtotal (net.) £ 5.00
    + VAT (20.0 %) £ 1.00
    Charges £ 6.00
    The total amount due will be charged to your card on file within the next seven days.
    """
    result = parse_extracted_text(
        DocumentExtractionResult(
            processing_status="completed",
            document_type="invoice",
            extracted_text=sample_text,
            parser_notes="test",
        )
    )

    assert result.supplier_guess == "IONOS"
    assert result.invoice_number_guess == "203054576536"
    assert result.invoice_date_guess == "08/04/2026"
    assert result.total_amount_guess == "£6.00"
    assert result.currency_guess == "GBP"


def test_build_document_description_for_ionos_contract_invoice() -> None:
    extracted_text = """
    IONOS Cloud Ltd.
    Invoice No.: 203054576536
    Contract: 111511617 - IONOS VPS Linux L+
    """
    description = build_document_description(
        document_type="invoice",
        supplier_name="IONOS",
        reference_number="203054576536",
        extracted_text=extracted_text,
        fallback_filename="invoice.pdf",
    )
    assert description == "IONOS VPS Linux L+ invoice 203054576536"


def test_build_extracted_text_preview_truncates_cleanly() -> None:
    preview = build_extracted_text_preview("A  B\nC " * 80, limit=60)
    assert preview.endswith("...")
    assert len(preview) <= 60
