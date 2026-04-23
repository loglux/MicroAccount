from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.documents.extract import extract_document
from app.documents.schemas import DocumentProcessingTask
from app.domain.models import Attachment, DocumentExtraction, IncomingDocument
from app.services.accounting import ExpenseInput, create_expense
from app.storage.files import (
    delete_stored_file,
    delete_temp_session,
    finalize_temp_upload,
    read_temp_session,
    store_temp_upload,
    write_temp_session,
)


@dataclass(slots=True)
class TempDocumentSession:
    id: str
    original_filename: str
    stored_filename: str
    mime_type: str | None
    file_size: int
    sha256: str
    storage_path: str
    processing_status: str
    document_type: str | None = None
    supplier_guess: str | None = None
    reference_number_guess: str | None = None
    document_date_guess: str | None = None
    total_amount_guess: str | None = None
    currency_guess: str | None = None
    confidence_score: str | None = None
    extracted_text: str | None = None
    parser_notes: str | None = None
    created_at: str = ""
    updated_at: str = ""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_document_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_document_amount(value: str | None) -> Decimal | None:
    if not value:
        return None
    cleaned = value.replace("£", "").replace("$", "").replace("€", "").replace(",", "").strip()
    return Decimal(cleaned) if cleaned else None


def create_temp_document_session(upload: UploadFile) -> TempDocumentSession | None:
    if not upload.filename:
        return None

    stored = store_temp_upload(upload)
    extraction = extract_document(
        DocumentProcessingTask(
            attachment_id=0,
            storage_path=stored.storage_path,
            mime_type=stored.mime_type,
        )
    )
    now = _now_iso()
    session = TempDocumentSession(
        id=stored.session_id,
        original_filename=stored.original_filename,
        stored_filename=stored.stored_filename,
        mime_type=stored.mime_type,
        file_size=stored.file_size,
        sha256=stored.sha256,
        storage_path=stored.storage_path,
        processing_status=extraction.processing_status,
        document_type=extraction.document_type,
        supplier_guess=extraction.supplier_guess,
        reference_number_guess=extraction.invoice_number_guess,
        document_date_guess=extraction.invoice_date_guess,
        total_amount_guess=extraction.total_amount_guess,
        currency_guess=extraction.currency_guess,
        confidence_score=extraction.confidence_score,
        extracted_text=extraction.extracted_text,
        parser_notes=extraction.parser_notes,
        created_at=now,
        updated_at=now,
    )
    write_temp_session(session.id, asdict(session))
    return session


def get_temp_document_session(session_id: str) -> TempDocumentSession | None:
    payload = read_temp_session(session_id)
    if payload is None:
        return None
    return TempDocumentSession(**payload)


def update_temp_document_session(
    session_id: str,
    document_type: str | None = None,
    supplier_guess: str | None = None,
    reference_number_guess: str | None = None,
    document_date_guess: str | None = None,
    total_amount_guess: str | None = None,
    currency_guess: str | None = None,
    parser_notes: str | None = None,
) -> TempDocumentSession:
    session = get_temp_document_session(session_id)
    if session is None:
        raise ValueError("Temporary document session not found.")

    session.document_type = document_type or None
    session.supplier_guess = supplier_guess or None
    session.reference_number_guess = reference_number_guess or None
    session.document_date_guess = document_date_guess or None
    session.total_amount_guess = total_amount_guess or None
    session.currency_guess = currency_guess or None
    session.parser_notes = parser_notes or session.parser_notes
    session.updated_at = _now_iso()
    write_temp_session(session.id, asdict(session))
    return session


def discard_temp_document_session(session_id: str) -> None:
    session = get_temp_document_session(session_id)
    if session is None:
        return
    delete_stored_file(session.storage_path)
    delete_temp_session(session_id)


def create_expense_from_temp_document(
    db: Session,
    session_id: str,
    category_code: str,
    description: str | None = None,
    supplier_name: str | None = None,
    expense_date: date | None = None,
    amount_gbp: Decimal | None = None,
    is_pre_trading: bool = False,
    incurred_before_incorporation: bool = False,
    cost_treatment: str = "revenue",
    use_type: str = "business_only",
    business_use_percent: Decimal | None = None,
    notes: str | None = None,
):
    session = get_temp_document_session(session_id)
    if session is None:
        raise ValueError("Temporary document session not found.")

    resolved_supplier = supplier_name or session.supplier_guess or None
    resolved_date = (
        expense_date or _parse_document_date(session.document_date_guess) or date.today()
    )
    resolved_amount = amount_gbp or _parse_document_amount(session.total_amount_guess)
    if resolved_amount is None:
        raise ValueError("Could not determine amount from document. Provide it manually.")

    resolved_description = description or (
        f"{session.document_type or 'document'} "
        f"{session.reference_number_guess or session.original_filename}"
    )

    expense = create_expense(
        db,
        ExpenseInput(
            expense_date=resolved_date,
            supplier_name=resolved_supplier,
            description=resolved_description,
            amount_gbp=resolved_amount,
            category_code=category_code,
            is_pre_trading=is_pre_trading,
            incurred_before_incorporation=incurred_before_incorporation,
            cost_treatment=cost_treatment,
            use_type=use_type,
            business_use_percent=business_use_percent,
            notes=notes,
        ),
        uploads=[],
    )

    stored = finalize_temp_upload(
        session.storage_path,
        original_filename=session.original_filename,
        mime_type=session.mime_type,
    )
    attachment = Attachment(
        expense_id=expense.id,
        original_filename=stored.original_filename,
        stored_filename=stored.stored_filename,
        mime_type=stored.mime_type,
        file_size=stored.file_size,
        sha256=stored.sha256,
        storage_path=stored.storage_path,
        document_role="primary_document",
        processing_status=session.processing_status,
        processing_error=None,
    )
    db.add(attachment)
    db.flush()
    db.add(
        DocumentExtraction(
            attachment_id=attachment.id,
            extractor_name="temp_document_import",
            processing_status=session.processing_status,
            document_type=session.document_type,
            extracted_text=session.extracted_text,
            supplier_guess=session.supplier_guess,
            invoice_number_guess=session.reference_number_guess,
            invoice_date_guess=session.document_date_guess,
            total_amount_guess=session.total_amount_guess,
            currency_guess=session.currency_guess,
            confidence_score=session.confidence_score,
            parser_notes=session.parser_notes,
        )
    )
    db.commit()
    delete_temp_session(session_id)
    return expense


def save_temp_document_to_holding(db: Session, session_id: str) -> IncomingDocument:
    session = get_temp_document_session(session_id)
    if session is None:
        raise ValueError("Temporary document session not found.")

    stored = finalize_temp_upload(
        session.storage_path,
        original_filename=session.original_filename,
        mime_type=session.mime_type,
    )
    document = IncomingDocument(
        original_filename=stored.original_filename,
        stored_filename=stored.stored_filename,
        mime_type=stored.mime_type,
        file_size=stored.file_size,
        sha256=stored.sha256,
        storage_path=stored.storage_path,
        processing_status=session.processing_status,
        document_type=session.document_type,
        supplier_guess=session.supplier_guess,
        reference_number_guess=session.reference_number_guess,
        document_date_guess=session.document_date_guess,
        total_amount_guess=session.total_amount_guess,
        currency_guess=session.currency_guess,
        confidence_score=session.confidence_score,
        extracted_text=session.extracted_text,
        parser_notes=session.parser_notes,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    delete_temp_session(session_id)
    return document
