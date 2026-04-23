from __future__ import annotations

from pypdf import PdfReader

from app.documents.parse import parse_extracted_text
from app.documents.schemas import DocumentExtractionResult, DocumentProcessingTask


def extract_document(task: DocumentProcessingTask) -> DocumentExtractionResult:
    if task.mime_type and "pdf" not in task.mime_type.lower():
        return DocumentExtractionResult(
            processing_status="skipped",
            parser_notes="Text extraction currently supports PDF attachments only.",
        )

    reader = PdfReader(task.storage_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    extracted_text = "\n".join(page.strip() for page in pages if page.strip()).strip()
    if not extracted_text:
        return DocumentExtractionResult(
            processing_status="empty",
            parser_notes="No extractable PDF text was found. OCR is likely required.",
        )

    result = DocumentExtractionResult(
        processing_status="completed",
        document_type="pdf_document",
        extracted_text=extracted_text,
        parser_notes="Text extracted from born-digital PDF without OCR.",
    )
    return parse_extracted_text(result)
