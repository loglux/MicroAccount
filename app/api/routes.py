from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import (
    ExpenseCreate,
    IncomingDocumentCreateExpense,
    IncomingDocumentReviewUpdate,
    RepaymentCreate,
)
from app.db.session import get_db
from app.exports.csv import export_director_loan_csv, export_expenses_csv
from app.exports.json_backup import export_backup_json
from app.services.accounting import (
    ExpenseInput,
    RepaymentInput,
    create_expense,
    create_expense_from_incoming_document,
    create_repayment,
    discard_incoming_document,
    get_attachment_prefill,
    get_expense_prefill_from_primary_attachment,
    get_incoming_document,
    get_summary,
    list_director_loan_entries,
    list_expenses,
    list_incoming_documents,
    update_incoming_document_review,
    upload_incoming_documents,
)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict[str, str | int]:
    data = get_summary(db)
    return {
        "total_loaned": f"{data.total_loaned:.2f}",
        "total_repaid": f"{data.total_repaid:.2f}",
        "balance_due_to_director": f"{data.balance_due_to_director:.2f}",
        "expense_count": data.expense_count,
        "attachment_count": data.attachment_count,
        "pre_trading_expense_count": data.pre_trading_expense_count,
    }


@router.get("/expenses")
def expenses(
    start_date: date | None = None,
    end_date: date | None = None,
    category_code: str | None = None,
    search_text: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    return [
        {
            "id": expense.id,
            "expense_date": expense.expense_date.isoformat(),
            "supplier_name": expense.supplier_name,
            "description": expense.description,
            "amount_gbp": f"{expense.amount_gbp:.2f}",
            "category_code": expense.category_code,
            "is_pre_trading": expense.is_pre_trading,
            "attachment_count": len(expense.attachments),
        }
        for expense in list_expenses(db, start_date, end_date, category_code, search_text)
    ]


@router.post("/expenses", status_code=201)
def create_expense_endpoint(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    expense = create_expense(
        db,
        ExpenseInput(
            expense_date=payload.expense_date,
            supplier_name=payload.supplier_name,
            description=payload.description,
            amount_gbp=payload.amount_gbp,
            category_code=payload.category_code,
            is_pre_trading=payload.is_pre_trading,
            incurred_before_incorporation=payload.incurred_before_incorporation,
            cost_treatment=payload.cost_treatment,
            use_type=payload.use_type,
            business_use_percent=payload.business_use_percent,
            notes=payload.notes,
            allowable_for_ct=payload.allowable_for_ct,
        ),
    )
    return {"id": expense.id, "description": expense.description}


@router.get("/director-loan")
def director_loan(
    start_date: date | None = None,
    end_date: date | None = None,
    search_text: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    return [
        {
            "id": row.entry.id,
            "entry_date": row.entry.entry_date.isoformat(),
            "entry_type": row.entry.entry_type,
            "direction": row.entry.direction,
            "amount_gbp": f"{row.entry.amount_gbp:.2f}",
            "reference": row.entry.reference,
            "expense_id": row.entry.expense_id,
            "running_balance": f"{row.running_balance:.2f}",
        }
        for row in list_director_loan_entries(db, start_date, end_date, search_text)
    ]


@router.post("/repayments", status_code=201)
def create_repayment_endpoint(
    payload: RepaymentCreate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    entry = create_repayment(
        db,
        RepaymentInput(
            entry_date=payload.entry_date,
            amount_gbp=payload.amount_gbp,
            reference=payload.reference,
            notes=payload.notes,
        ),
    )
    return {"id": entry.id, "reference": entry.reference}


@router.post("/exports/refresh")
def refresh_exports(db: Session = Depends(get_db)) -> dict[str, str]:
    export_expenses_csv(db)
    export_director_loan_csv(db)
    export_backup_json(db)
    return {"status": "ok"}


@router.get("/attachments/{attachment_id}/prefill")
def attachment_prefill(
    attachment_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    return get_attachment_prefill(db, attachment_id)


@router.get("/expenses/{expense_id}/prefill")
def expense_prefill(
    expense_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    return get_expense_prefill_from_primary_attachment(db, expense_id)


@router.get("/incoming-documents")
def incoming_documents(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return [
        {
            "id": document.id,
            "original_filename": document.original_filename,
            "processing_status": document.processing_status,
            "document_type": document.document_type,
            "supplier_guess": document.supplier_guess,
            "reference_number_guess": document.reference_number_guess,
            "document_date_guess": document.document_date_guess,
            "total_amount_guess": document.total_amount_guess,
            "currency_guess": document.currency_guess,
            "linked_expense_id": document.linked_expense_id,
        }
        for document in list_incoming_documents(db)
    ]


@router.post("/incoming-documents/upload", status_code=201)
async def upload_incoming_documents_endpoint(
    documents: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    uploaded = upload_incoming_documents(db, documents)
    return [
        {
            "id": document.id,
            "original_filename": document.original_filename,
            "processing_status": document.processing_status,
            "document_type": document.document_type,
        }
        for document in uploaded
    ]


@router.get("/incoming-documents/{document_id}")
def incoming_document(document_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    document = get_incoming_document(db, document_id)
    if document is None:
        return {}
    return {
        "id": document.id,
        "original_filename": document.original_filename,
        "processing_status": document.processing_status,
        "document_type": document.document_type,
        "supplier_guess": document.supplier_guess,
        "reference_number_guess": document.reference_number_guess,
        "document_date_guess": document.document_date_guess,
        "total_amount_guess": document.total_amount_guess,
        "currency_guess": document.currency_guess,
        "confidence_score": document.confidence_score,
        "linked_expense_id": document.linked_expense_id,
    }


@router.delete("/incoming-documents/{document_id}", status_code=204)
def discard_incoming_document_endpoint(document_id: int, db: Session = Depends(get_db)) -> None:
    try:
        deleted = discard_incoming_document(db, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Incoming document not found.")


@router.post("/incoming-documents/{document_id}/review")
def update_incoming_document_review_endpoint(
    document_id: int,
    payload: IncomingDocumentReviewUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    document = update_incoming_document_review(
        db,
        document_id=document_id,
        document_type=payload.document_type,
        supplier_guess=payload.supplier_guess,
        reference_number_guess=payload.reference_number_guess,
        document_date_guess=payload.document_date_guess,
        total_amount_guess=payload.total_amount_guess,
        currency_guess=payload.currency_guess,
        parser_notes=payload.parser_notes,
    )
    return {"id": document.id, "processing_status": document.processing_status}


@router.post("/incoming-documents/{document_id}/create-expense", status_code=201)
def create_expense_from_document_endpoint(
    document_id: int,
    payload: IncomingDocumentCreateExpense,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    expense = create_expense_from_incoming_document(
        db,
        document_id=document_id,
        category_code=payload.category_code,
        description=payload.description,
        supplier_name=payload.supplier_name,
        expense_date=payload.expense_date,
        amount_gbp=payload.amount_gbp,
        is_pre_trading=payload.is_pre_trading,
        incurred_before_incorporation=payload.incurred_before_incorporation,
        cost_treatment=payload.cost_treatment,
        use_type=payload.use_type,
        business_use_percent=payload.business_use_percent,
        notes=payload.notes,
    )
    return {"expense_id": expense.id}
