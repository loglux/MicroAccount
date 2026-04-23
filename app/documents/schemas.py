from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DocumentProcessingTask:
    attachment_id: int
    storage_path: str
    mime_type: str | None


@dataclass(slots=True)
class DocumentExtractionResult:
    processing_status: str
    document_type: str | None = None
    extracted_text: str | None = None
    supplier_guess: str | None = None
    invoice_number_guess: str | None = None
    invoice_date_guess: str | None = None
    total_amount_guess: str | None = None
    currency_guess: str | None = None
    confidence_score: str | None = None
    parser_notes: str | None = None
