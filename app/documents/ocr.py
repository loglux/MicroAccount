from __future__ import annotations

from app.documents.schemas import DocumentExtractionResult, DocumentProcessingTask


def run_ocr(task: DocumentProcessingTask) -> DocumentExtractionResult:
    return DocumentExtractionResult(
        processing_status="pending",
        parser_notes=(
            "OCR backend not configured yet. "
            "This module is reserved for scanned PDF and receipt recognition."
        ),
    )
