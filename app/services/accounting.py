from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.documents.extract import extract_document
from app.documents.ingest import build_processing_task
from app.documents.schemas import DocumentProcessingTask
from app.domain.models import (
    AccountMapping,
    Attachment,
    DirectorLoanEntry,
    DocumentExtraction,
    Expense,
    IncomingDocument,
)
from app.domain.policies.uk import (
    DEFAULT_ACCOUNT_MAPPINGS,
    DEFAULT_CATEGORIES,
    DIRECTOR_LOAN_EXPENSE_TYPE,
    DIRECTOR_PAID_METHOD,
    DLA_LOAN_TO_COMPANY,
    DLA_REPAYMENT_TO_DIRECTOR,
    GBP,
    build_expense_loan_reference,
    director_loan_balance,
)
from app.storage.files import delete_stored_file, store_existing_file, store_upload


@dataclass(slots=True)
class DlaSummary:
    total_loaned: Decimal
    total_repaid: Decimal
    balance_due_to_director: Decimal
    expense_count: int
    attachment_count: int
    pre_trading_expense_count: int


@dataclass(slots=True)
class LedgerRow:
    entry: DirectorLoanEntry
    running_balance: Decimal


@dataclass(slots=True)
class ExpenseInput:
    expense_date: date
    supplier_name: str | None
    description: str
    amount_gbp: Decimal
    category_code: str
    is_pre_trading: bool = False
    incurred_before_incorporation: bool = False
    cost_treatment: str = "revenue"
    use_type: str = "business_only"
    business_use_percent: Decimal | None = None
    notes: str | None = None
    allowable_for_ct: bool | None = None


@dataclass(slots=True)
class RepaymentInput:
    entry_date: date
    amount_gbp: Decimal
    reference: str
    notes: str | None = None


@dataclass(slots=True)
class ExpenseUpdateInput:
    expense_date: date
    supplier_name: str | None
    description: str
    amount_gbp: Decimal
    category_code: str
    is_pre_trading: bool = False
    incurred_before_incorporation: bool = False
    cost_treatment: str = "revenue"
    use_type: str = "business_only"
    business_use_percent: Decimal | None = None
    notes: str | None = None


def list_categories() -> list[str]:
    return DEFAULT_CATEGORIES.copy()


def ensure_account_mapping_seed_data(db: Session) -> None:
    existing_count = db.scalar(select(func.count()).select_from(AccountMapping)) or 0
    if existing_count:
        return

    for category_code, (account_code, account_name) in DEFAULT_ACCOUNT_MAPPINGS.items():
        db.add(
            AccountMapping(
                category_code=category_code,
                account_code=account_code,
                account_name=account_name,
            )
        )
    db.commit()


def get_account_mapping_for_category(
    db: Session,
    category_code: str,
) -> AccountMapping | None:
    ensure_account_mapping_seed_data(db)
    return db.scalar(select(AccountMapping).where(AccountMapping.category_code == category_code))


def list_account_mappings(db: Session) -> list[AccountMapping]:
    ensure_account_mapping_seed_data(db)
    return list(
        db.scalars(select(AccountMapping).order_by(AccountMapping.account_code.asc())).all()
    )


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
    if not cleaned:
        return None
    return Decimal(cleaned)


def create_expense(
    db: Session,
    payload: ExpenseInput,
    uploads: list[UploadFile] | None = None,
) -> Expense:
    normalized_business_use_percent = payload.business_use_percent
    if normalized_business_use_percent is None:
        normalized_business_use_percent = Decimal("100.00")

    needs_review = any(
        (
            payload.incurred_before_incorporation,
            payload.cost_treatment != "revenue",
            payload.use_type != "business_only",
            normalized_business_use_percent != Decimal("100.00"),
        )
    )
    expense = Expense(
        expense_date=payload.expense_date,
        supplier_name=payload.supplier_name,
        description=payload.description.strip(),
        amount_gbp=payload.amount_gbp,
        currency=GBP,
        category_code=payload.category_code,
        paid_by=DIRECTOR_PAID_METHOD,
        expense_type=DIRECTOR_LOAN_EXPENSE_TYPE,
        is_pre_trading=payload.is_pre_trading,
        incurred_before_incorporation=payload.incurred_before_incorporation,
        cost_treatment=payload.cost_treatment,
        use_type=payload.use_type,
        business_use_percent=normalized_business_use_percent,
        needs_review=needs_review,
        is_business_use=payload.use_type == "business_only",
        allowable_for_ct=payload.allowable_for_ct,
        status="needs_review" if needs_review else "recorded",
        notes=payload.notes,
    )
    db.add(expense)
    db.flush()

    loan_entry = DirectorLoanEntry(
        entry_date=payload.expense_date,
        entry_type=DIRECTOR_LOAN_EXPENSE_TYPE,
        direction=DLA_LOAN_TO_COMPANY,
        amount_gbp=payload.amount_gbp,
        reference=build_expense_loan_reference(expense.id, payload.description),
        expense_id=expense.id,
        notes="Auto-created from business expense paid personally by the director.",
    )
    db.add(loan_entry)

    created_attachment_count = 0
    for upload in uploads or []:
        if not upload.filename:
            continue
        stored = store_upload(upload)
        document_role = (
            "primary_document" if created_attachment_count == 0 else "supporting_document"
        )
        attachment = Attachment(
            expense_id=expense.id,
            original_filename=stored.original_filename,
            stored_filename=stored.stored_filename,
            mime_type=stored.mime_type,
            file_size=stored.file_size,
            sha256=stored.sha256,
            storage_path=stored.storage_path,
            document_role=document_role,
            processing_status="queued",
        )
        db.add(attachment)
        db.flush()
        extraction_result = extract_document(build_processing_task(attachment))
        attachment.processing_status = extraction_result.processing_status
        attachment.processing_error = None
        db.add(
            DocumentExtraction(
                attachment_id=attachment.id,
                extractor_name="document_pipeline",
                processing_status=extraction_result.processing_status,
                document_type=extraction_result.document_type,
                extracted_text=extraction_result.extracted_text,
                supplier_guess=extraction_result.supplier_guess,
                invoice_number_guess=extraction_result.invoice_number_guess,
                invoice_date_guess=extraction_result.invoice_date_guess,
                total_amount_guess=extraction_result.total_amount_guess,
                currency_guess=extraction_result.currency_guess,
                confidence_score=extraction_result.confidence_score,
                parser_notes=extraction_result.parser_notes,
            )
        )
        created_attachment_count += 1

    db.commit()
    return db.scalar(
        select(Expense).options(selectinload(Expense.attachments)).where(Expense.id == expense.id)
    )


def create_repayment(db: Session, payload: RepaymentInput) -> DirectorLoanEntry:
    entry = DirectorLoanEntry(
        entry_date=payload.entry_date,
        entry_type=DLA_REPAYMENT_TO_DIRECTOR,
        direction=DLA_REPAYMENT_TO_DIRECTOR,
        amount_gbp=payload.amount_gbp,
        reference=payload.reference.strip(),
        notes=payload.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def upload_incoming_documents(
    db: Session,
    uploads: list[UploadFile],
) -> list[IncomingDocument]:
    documents: list[IncomingDocument] = []
    for upload in uploads:
        if not upload.filename:
            continue
        stored = store_upload(upload)
        extraction_result = extract_document(
            DocumentProcessingTask(
                attachment_id=0,
                storage_path=str(settings.project_root / stored.storage_path),
                mime_type=stored.mime_type,
            )
        )
        document = IncomingDocument(
            original_filename=stored.original_filename,
            stored_filename=stored.stored_filename,
            mime_type=stored.mime_type,
            file_size=stored.file_size,
            sha256=stored.sha256,
            storage_path=stored.storage_path,
            processing_status=extraction_result.processing_status,
            document_type=extraction_result.document_type,
            supplier_guess=extraction_result.supplier_guess,
            reference_number_guess=extraction_result.invoice_number_guess,
            document_date_guess=extraction_result.invoice_date_guess,
            total_amount_guess=extraction_result.total_amount_guess,
            currency_guess=extraction_result.currency_guess,
            confidence_score=extraction_result.confidence_score,
            extracted_text=extraction_result.extracted_text,
            parser_notes=extraction_result.parser_notes,
        )
        db.add(document)
        db.flush()
        documents.append(document)
    db.commit()
    for document in documents:
        db.refresh(document)
    return documents


def list_incoming_documents(db: Session) -> list[IncomingDocument]:
    return db.scalars(
        select(IncomingDocument).order_by(
            IncomingDocument.created_at.desc(), IncomingDocument.id.desc()
        )
    ).all()


def get_incoming_document(db: Session, document_id: int) -> IncomingDocument | None:
    return db.get(IncomingDocument, document_id)


def discard_incoming_document(db: Session, document_id: int) -> bool:
    document = db.get(IncomingDocument, document_id)
    if document is None:
        return False
    if document.linked_expense_id is not None:
        raise ValueError("Linked incoming documents cannot be discarded.")

    storage_path = document.storage_path
    db.delete(document)
    db.commit()
    delete_stored_file(storage_path)
    return True


def update_incoming_document_review(
    db: Session,
    document_id: int,
    document_type: str | None = None,
    supplier_guess: str | None = None,
    reference_number_guess: str | None = None,
    document_date_guess: str | None = None,
    total_amount_guess: str | None = None,
    currency_guess: str | None = None,
    parser_notes: str | None = None,
) -> IncomingDocument:
    document = db.get(IncomingDocument, document_id)
    if document is None:
        raise ValueError("Incoming document not found.")

    document.document_type = document_type or None
    document.supplier_guess = supplier_guess or None
    document.reference_number_guess = reference_number_guess or None
    document.document_date_guess = document_date_guess or None
    document.total_amount_guess = total_amount_guess or None
    document.currency_guess = currency_guess or None
    document.parser_notes = parser_notes or document.parser_notes
    document.updated_at = datetime.now()
    db.commit()
    db.refresh(document)
    return document


def create_expense_from_incoming_document(
    db: Session,
    document_id: int,
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
) -> Expense:
    document = db.get(IncomingDocument, document_id)
    if document is None:
        raise ValueError("Incoming document not found.")
    if document.linked_expense_id is not None:
        linked_expense = db.get(Expense, document.linked_expense_id)
        if linked_expense is not None:
            return linked_expense

    resolved_supplier = supplier_name or document.supplier_guess or None
    resolved_date = (
        expense_date or _parse_document_date(document.document_date_guess) or date.today()
    )
    resolved_amount = amount_gbp or _parse_document_amount(document.total_amount_guess)
    if resolved_amount is None:
        raise ValueError("Could not determine amount from document. Provide it manually.")

    resolved_description = description or (
        f"{document.document_type or 'document'} "
        f"{document.reference_number_guess or document.original_filename}"
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

    attachment = Attachment(
        expense_id=expense.id,
        original_filename=document.original_filename,
        stored_filename=document.stored_filename,
        mime_type=document.mime_type,
        file_size=document.file_size,
        sha256=document.sha256,
        storage_path=document.storage_path,
        document_role="primary_document",
        processing_status=document.processing_status,
        processing_error=None,
    )
    db.add(attachment)
    db.flush()
    db.add(
        DocumentExtraction(
            attachment_id=attachment.id,
            extractor_name="incoming_document_import",
            processing_status=document.processing_status,
            document_type=document.document_type,
            extracted_text=document.extracted_text,
            supplier_guess=document.supplier_guess,
            invoice_number_guess=document.reference_number_guess,
            invoice_date_guess=document.document_date_guess,
            total_amount_guess=document.total_amount_guess,
            currency_guess=document.currency_guess,
            confidence_score=document.confidence_score,
            parser_notes=document.parser_notes,
        )
    )
    document.linked_expense_id = expense.id
    document.processing_status = "converted"
    db.commit()
    db.refresh(expense)
    return expense


def attach_files_to_expense(
    db: Session,
    expense_id: int,
    file_paths: list[Path],
) -> list[Attachment]:
    attachments: list[Attachment] = []
    existing_attachment_count = int(
        db.scalar(
            select(func.count()).select_from(Attachment).where(Attachment.expense_id == expense_id)
        )
        or 0
    )

    for file_path in file_paths:
        stored = store_existing_file(file_path)
        document_role = (
            "primary_document" if existing_attachment_count == 0 else "supporting_document"
        )
        attachment = Attachment(
            expense_id=expense_id,
            original_filename=stored.original_filename,
            stored_filename=stored.stored_filename,
            mime_type=stored.mime_type,
            file_size=stored.file_size,
            sha256=stored.sha256,
            storage_path=stored.storage_path,
            document_role=document_role,
            processing_status="queued",
        )
        db.add(attachment)
        db.flush()
        extraction_result = extract_document(build_processing_task(attachment))
        attachment.processing_status = extraction_result.processing_status
        attachment.processing_error = None
        db.add(
            DocumentExtraction(
                attachment_id=attachment.id,
                extractor_name="document_pipeline",
                processing_status=extraction_result.processing_status,
                document_type=extraction_result.document_type,
                extracted_text=extraction_result.extracted_text,
                supplier_guess=extraction_result.supplier_guess,
                invoice_number_guess=extraction_result.invoice_number_guess,
                invoice_date_guess=extraction_result.invoice_date_guess,
                total_amount_guess=extraction_result.total_amount_guess,
                currency_guess=extraction_result.currency_guess,
                confidence_score=extraction_result.confidence_score,
                parser_notes=extraction_result.parser_notes,
            )
        )
        attachments.append(attachment)
        existing_attachment_count += 1

    db.commit()
    for attachment in attachments:
        db.refresh(attachment)
    return attachments


def get_summary(db: Session) -> DlaSummary:
    total_loaned = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(DirectorLoanEntry.amount_gbp), 0)).where(
                DirectorLoanEntry.direction == DLA_LOAN_TO_COMPANY
            )
        )
    )
    total_repaid = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(DirectorLoanEntry.amount_gbp), 0)).where(
                DirectorLoanEntry.direction == DLA_REPAYMENT_TO_DIRECTOR
            )
        )
    )
    expense_count = int(db.scalar(select(func.count()).select_from(Expense)) or 0)
    attachment_count = int(db.scalar(select(func.count()).select_from(Attachment)) or 0)
    pre_trading_expense_count = int(
        db.scalar(select(func.count()).select_from(Expense).where(Expense.is_pre_trading.is_(True)))
        or 0
    )
    return DlaSummary(
        total_loaned=total_loaned,
        total_repaid=total_repaid,
        balance_due_to_director=director_loan_balance(total_loaned, total_repaid),
        expense_count=expense_count,
        attachment_count=attachment_count,
        pre_trading_expense_count=pre_trading_expense_count,
    )


def list_expenses(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    category_code: str | None = None,
    search_text: str | None = None,
) -> list[Expense]:
    query = (
        select(Expense)
        .options(selectinload(Expense.attachments))
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
    )
    if start_date:
        query = query.where(Expense.expense_date >= start_date)
    if end_date:
        query = query.where(Expense.expense_date <= end_date)
    if category_code:
        query = query.where(Expense.category_code == category_code)
    if search_text:
        search_pattern = f"%{search_text.strip()}%"
        query = query.where(
            or_(
                Expense.description.ilike(search_pattern),
                Expense.supplier_name.ilike(search_pattern),
                Expense.notes.ilike(search_pattern),
            )
        )
    return db.scalars(query).all()


def list_director_loan_entries(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    search_text: str | None = None,
) -> list[LedgerRow]:
    query = select(DirectorLoanEntry).order_by(
        DirectorLoanEntry.entry_date.asc(),
        DirectorLoanEntry.id.asc(),
    )
    if start_date:
        query = query.where(DirectorLoanEntry.entry_date >= start_date)
    if end_date:
        query = query.where(DirectorLoanEntry.entry_date <= end_date)
    if search_text:
        search_pattern = f"%{search_text.strip()}%"
        query = query.where(
            or_(
                DirectorLoanEntry.reference.ilike(search_pattern),
                DirectorLoanEntry.notes.ilike(search_pattern),
            )
        )
    entries = db.scalars(query).all()

    running_balance = Decimal("0.00")
    rows: list[LedgerRow] = []
    for entry in entries:
        if entry.direction == DLA_LOAN_TO_COMPANY:
            running_balance += Decimal(entry.amount_gbp)
        else:
            running_balance -= Decimal(entry.amount_gbp)
        rows.append(LedgerRow(entry=entry, running_balance=running_balance))

    rows.reverse()
    return rows


def get_attachment_prefill(db: Session, attachment_id: int) -> dict[str, str | None]:
    extraction = db.scalar(
        select(DocumentExtraction)
        .join(Attachment, Attachment.id == DocumentExtraction.attachment_id)
        .where(Attachment.id == attachment_id)
        .order_by(DocumentExtraction.updated_at.desc(), DocumentExtraction.id.desc())
    )
    if extraction is None:
        return {}
    return {
        "document_type": extraction.document_type,
        "supplier_name": extraction.supplier_guess,
        "reference_number": extraction.invoice_number_guess,
        "document_date": extraction.invoice_date_guess,
        "amount": extraction.total_amount_guess,
        "currency": extraction.currency_guess,
        "confidence_score": extraction.confidence_score,
    }


def get_expense_prefill_from_primary_attachment(
    db: Session,
    expense_id: int,
) -> dict[str, str | None]:
    primary_attachment = db.scalar(
        select(Attachment)
        .where(Attachment.expense_id == expense_id)
        .where(Attachment.document_role == "primary_document")
        .order_by(Attachment.id.asc())
    )
    if primary_attachment is None:
        primary_attachment = db.scalar(
            select(Attachment)
            .where(Attachment.expense_id == expense_id)
            .order_by(Attachment.id.asc())
        )
    if primary_attachment is None:
        return {}
    payload = get_attachment_prefill(db, primary_attachment.id)
    payload["attachment_id"] = str(primary_attachment.id)
    payload["document_role"] = primary_attachment.document_role
    return payload


def get_expense(db: Session, expense_id: int) -> Expense | None:
    return db.scalar(
        select(Expense)
        .options(
            selectinload(Expense.attachments),
            selectinload(Expense.loan_entries),
        )
        .where(Expense.id == expense_id)
    )


def update_expense(
    db: Session,
    expense_id: int,
    payload: ExpenseUpdateInput,
) -> Expense:
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise ValueError("Expense not found.")

    normalized_business_use_percent = payload.business_use_percent
    if normalized_business_use_percent is None:
        normalized_business_use_percent = Decimal("100.00")

    needs_review = any(
        (
            payload.incurred_before_incorporation,
            payload.cost_treatment != "revenue",
            payload.use_type != "business_only",
            normalized_business_use_percent != Decimal("100.00"),
        )
    )

    expense.expense_date = payload.expense_date
    expense.supplier_name = payload.supplier_name or None
    expense.description = payload.description.strip()
    expense.amount_gbp = payload.amount_gbp
    expense.category_code = payload.category_code
    expense.is_pre_trading = payload.is_pre_trading
    expense.incurred_before_incorporation = payload.incurred_before_incorporation
    expense.cost_treatment = payload.cost_treatment
    expense.use_type = payload.use_type
    expense.business_use_percent = normalized_business_use_percent
    expense.needs_review = needs_review
    expense.is_business_use = payload.use_type == "business_only"
    expense.status = "needs_review" if needs_review else "recorded"
    expense.notes = payload.notes
    expense.updated_at = datetime.now(UTC)

    loan_entry = db.scalar(
        select(DirectorLoanEntry)
        .where(DirectorLoanEntry.expense_id == expense_id)
        .where(DirectorLoanEntry.direction == DLA_LOAN_TO_COMPANY)
        .order_by(DirectorLoanEntry.id.asc())
    )
    if loan_entry is not None:
        loan_entry.amount_gbp = payload.amount_gbp
        loan_entry.entry_date = payload.expense_date
        loan_entry.reference = build_expense_loan_reference(expense_id, payload.description)

    db.commit()
    return db.scalar(
        select(Expense)
        .options(selectinload(Expense.attachments), selectinload(Expense.loan_entries))
        .where(Expense.id == expense_id)
    )


def delete_expense(db: Session, expense_id: int) -> bool:
    expense = db.get(Expense, expense_id)
    if expense is None:
        return False

    attachments = list(
        db.scalars(select(Attachment).where(Attachment.expense_id == expense_id)).all()
    )
    attachment_ids = [a.id for a in attachments]
    attachment_paths = [a.storage_path for a in attachments]

    if attachment_ids:
        db.execute(
            delete(DocumentExtraction).where(
                DocumentExtraction.attachment_id.in_(attachment_ids)
            )
        )
    db.execute(delete(Attachment).where(Attachment.expense_id == expense_id))
    db.execute(delete(DirectorLoanEntry).where(DirectorLoanEntry.expense_id == expense_id))

    for incoming in db.scalars(
        select(IncomingDocument).where(IncomingDocument.linked_expense_id == expense_id)
    ).all():
        incoming.linked_expense_id = None

    db.delete(expense)
    db.commit()

    for path in attachment_paths:
        delete_stored_file(path)

    return True


def attach_uploads_to_expense(
    db: Session,
    expense_id: int,
    uploads: list[UploadFile],
) -> list[Attachment]:
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise ValueError("Expense not found.")

    existing_attachment_count = int(
        db.scalar(
            select(func.count()).select_from(Attachment).where(Attachment.expense_id == expense_id)
        )
        or 0
    )

    attachments: list[Attachment] = []
    for upload in uploads:
        if not upload.filename:
            continue
        stored = store_upload(upload)
        document_role = (
            "primary_document" if existing_attachment_count == 0 else "supporting_document"
        )
        attachment = Attachment(
            expense_id=expense_id,
            original_filename=stored.original_filename,
            stored_filename=stored.stored_filename,
            mime_type=stored.mime_type,
            file_size=stored.file_size,
            sha256=stored.sha256,
            storage_path=stored.storage_path,
            document_role=document_role,
            processing_status="queued",
        )
        db.add(attachment)
        db.flush()
        extraction_result = extract_document(build_processing_task(attachment))
        attachment.processing_status = extraction_result.processing_status
        attachment.processing_error = None
        db.add(
            DocumentExtraction(
                attachment_id=attachment.id,
                extractor_name="document_pipeline",
                processing_status=extraction_result.processing_status,
                document_type=extraction_result.document_type,
                extracted_text=extraction_result.extracted_text,
                supplier_guess=extraction_result.supplier_guess,
                invoice_number_guess=extraction_result.invoice_number_guess,
                invoice_date_guess=extraction_result.invoice_date_guess,
                total_amount_guess=extraction_result.total_amount_guess,
                currency_guess=extraction_result.currency_guess,
                confidence_score=extraction_result.confidence_score,
                parser_notes=extraction_result.parser_notes,
            )
        )
        attachments.append(attachment)
        existing_attachment_count += 1

    db.commit()
    for attachment in attachments:
        db.refresh(attachment)
    return attachments


def remove_attachment(db: Session, attachment_id: int) -> bool:
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        return False
    storage_path = attachment.storage_path
    db.execute(
        delete(DocumentExtraction).where(DocumentExtraction.attachment_id == attachment_id)
    )
    db.delete(attachment)
    db.commit()
    delete_stored_file(storage_path)
    return True
