from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.documents.parse import build_document_description, build_extracted_text_preview
from app.documents.temp_sessions import (
    create_expense_from_temp_document,
    create_temp_document_session,
    discard_temp_document_session,
    get_temp_document_session,
    save_temp_document_to_holding,
    update_temp_document_session,
)
from app.exports.csv import export_director_loan_csv, export_expenses_csv
from app.exports.json_backup import export_backup_json
from app.services.accounting import (
    ExpenseInput,
    RepaymentInput,
    create_expense,
    create_expense_from_incoming_document,
    create_repayment,
    discard_incoming_document,
    get_expense_prefill_from_primary_attachment,
    get_incoming_document,
    get_summary,
    list_account_mappings,
    list_categories,
    list_director_loan_entries,
    list_expenses,
    list_incoming_documents,
    update_incoming_document_review,
)
from app.services.income import (
    IncomeInput,
    create_income,
    get_income_summary,
    list_income_records,
)
from app.services.labels import humanize

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
templates.env.filters["humanize"] = humanize


def normalize_prefill_date(value: str | None) -> str:
    if not value:
        return ""
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def normalize_prefill_amount(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("£", "").replace("$", "").replace("€", "").strip()


def normalize_business_use_percent(value: str | None) -> str:
    return value or "100.00"


def default_document_description(
    *,
    document_type: str | None,
    supplier_name: str | None,
    reference_number: str | None,
    extracted_text: str | None,
    fallback_filename: str | None,
) -> str:
    return build_document_description(
        document_type=document_type,
        supplier_name=supplier_name,
        reference_number=reference_number,
        extracted_text=extracted_text,
        fallback_filename=fallback_filename,
    )


def common_page_context(
    *,
    request: Request,
    db: Session,
    active_page: str,
    start_date: date | None = None,
    end_date: date | None = None,
    category_code: str | None = None,
    search_text: str | None = None,
    prefill_expense_id: int | None = None,
    review_document_id: int | None = None,
    review_temp_id: str | None = None,
) -> dict[str, object]:
    selected_prefill = (
        get_expense_prefill_from_primary_attachment(db, prefill_expense_id)
        if prefill_expense_id is not None
        else {}
    )
    selected_document = (
        get_incoming_document(db, review_document_id) if review_document_id is not None else None
    )
    selected_temp_document = (
        get_temp_document_session(review_temp_id) if review_temp_id is not None else None
    )
    form_defaults = {
        "expense_date": normalize_prefill_date(selected_prefill.get("document_date")),
        "supplier_name": selected_prefill.get("supplier_name") or "",
        "description": "",
        "amount_gbp": normalize_prefill_amount(selected_prefill.get("amount")),
        "category_code": "",
        "incurred_before_incorporation": False,
        "cost_treatment": "revenue",
        "use_type": "business_only",
        "business_use_percent": "100.00",
        "notes": "",
    }
    return {
        "request": request,
        "app_name": settings.app_name,
        "active_page": active_page,
        "summary": get_summary(db),
        "expenses": list_expenses(db, start_date, end_date, category_code, search_text),
        "incoming_documents": list_incoming_documents(db),
        "selected_document": selected_document,
        "selected_temp_document": selected_temp_document,
        "selected_document_form_date": (
            normalize_prefill_date(selected_document.document_date_guess)
            if selected_document
            else ""
        ),
        "selected_document_description": (
            default_document_description(
                document_type=selected_document.document_type,
                supplier_name=selected_document.supplier_guess,
                reference_number=selected_document.reference_number_guess,
                extracted_text=selected_document.extracted_text,
                fallback_filename=selected_document.original_filename,
            )
            if selected_document
            else ""
        ),
        "selected_document_text_preview": (
            build_extracted_text_preview(selected_document.extracted_text)
            if selected_document
            else ""
        ),
        "selected_temp_document_form_date": (
            normalize_prefill_date(selected_temp_document.document_date_guess)
            if selected_temp_document
            else ""
        ),
        "selected_temp_document_description": (
            default_document_description(
                document_type=selected_temp_document.document_type,
                supplier_name=selected_temp_document.supplier_guess,
                reference_number=selected_temp_document.reference_number_guess,
                extracted_text=selected_temp_document.extracted_text,
                fallback_filename=selected_temp_document.original_filename,
            )
            if selected_temp_document
            else ""
        ),
        "selected_temp_document_text_preview": (
            build_extracted_text_preview(selected_temp_document.extracted_text)
            if selected_temp_document
            else ""
        ),
        "loan_rows": list_director_loan_entries(db, start_date, end_date, search_text),
        "categories": list_categories(),
        "selected_prefill": selected_prefill,
        "account_mappings": {
            mapping.category_code: f"{mapping.account_code} {mapping.account_name}"
            for mapping in list_account_mappings(db)
        },
        "form_defaults": form_defaults,
        "filters": {
            "start_date": start_date.isoformat() if start_date else "",
            "end_date": end_date.isoformat() if end_date else "",
            "category_code": category_code or "",
            "search_text": search_text or "",
        },
    }


@router.get("/")
def dashboard(
    request: Request,
):
    return RedirectResponse(url="/expenses", status_code=303)


@router.get("/expenses")
def expenses_page(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    category_code: str | None = None,
    search_text: str | None = None,
    prefill_expense_id: int | None = None,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="expenses.html",
        context=common_page_context(
            request=request,
            db=db,
            active_page="expenses",
            start_date=start_date,
            end_date=end_date,
            category_code=category_code,
            search_text=search_text,
            prefill_expense_id=prefill_expense_id,
        ),
    )


@router.get("/documents")
def documents_page(
    request: Request,
    review_document_id: int | None = None,
    review_temp_id: str | None = None,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="documents.html",
        context=common_page_context(
            request=request,
            db=db,
            active_page="documents",
            review_document_id=review_document_id,
            review_temp_id=review_temp_id,
        ),
    )


@router.get("/dla")
def dla_page(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    search_text: str | None = None,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="dla.html",
        context=common_page_context(
            request=request,
            db=db,
            active_page="dla",
            start_date=start_date,
            end_date=end_date,
            search_text=search_text,
        ),
    )


@router.post("/expenses")
async def create_expense_form(
    expense_date: date = Form(...),
    supplier_name: str | None = Form(default=None),
    description: str = Form(...),
    amount_gbp: Decimal = Form(...),
    category_code: str = Form(...),
    is_pre_trading: bool = Form(default=False),
    incurred_before_incorporation: bool = Form(default=False),
    cost_treatment: str = Form(default="revenue"),
    use_type: str = Form(default="business_only"),
    business_use_percent: Decimal | None = Form(default=None),
    notes: str | None = Form(default=None),
    attachments: list[UploadFile] = File(default=[]),
    redirect_to: str = Form(default="/expenses"),
    db: Session = Depends(get_db),
):
    create_expense(
        db,
        ExpenseInput(
            expense_date=expense_date,
            supplier_name=supplier_name,
            description=description,
            amount_gbp=amount_gbp,
            category_code=category_code,
            is_pre_trading=is_pre_trading,
            incurred_before_incorporation=incurred_before_incorporation,
            cost_treatment=cost_treatment,
            use_type=use_type,
            business_use_percent=business_use_percent,
            notes=notes,
        ),
        uploads=attachments,
    )
    return RedirectResponse(url=redirect_to, status_code=303)


@router.get("/income")
def income_page(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    search_text: str | None = None,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="income.html",
        context={
            "request": request,
            "app_name": settings.app_name,
            "active_page": "income",
            "income_records": list_income_records(db, start_date, end_date, search_text),
            "income_summary": get_income_summary(db),
            "filters": {
                "start_date": start_date.isoformat() if start_date else "",
                "end_date": end_date.isoformat() if end_date else "",
                "search_text": search_text or "",
            },
        },
    )


@router.post("/income")
async def create_income_form(
    income_date: date = Form(...),
    source_name: str = Form(...),
    description: str = Form(...),
    amount_gbp: Decimal = Form(...),
    reference: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    create_income(
        db,
        IncomeInput(
            income_date=income_date,
            source_name=source_name,
            description=description,
            amount_gbp=amount_gbp,
            reference=reference,
            notes=notes,
        ),
    )
    return RedirectResponse(url="/income", status_code=303)


@router.post("/repayments")
async def create_repayment_form(
    entry_date: date = Form(...),
    amount_gbp: Decimal = Form(...),
    reference: str = Form(...),
    notes: str | None = Form(default=None),
    redirect_to: str = Form(default="/dla"),
    db: Session = Depends(get_db),
):
    create_repayment(
        db,
        RepaymentInput(
            entry_date=entry_date,
            amount_gbp=amount_gbp,
            reference=reference,
            notes=notes,
        ),
    )
    return RedirectResponse(url=redirect_to, status_code=303)


@router.post("/documents/upload")
async def upload_documents_form(
    documents: UploadFile = File(...),
):
    session = create_temp_document_session(documents)
    if session is None:
        return RedirectResponse(url="/documents", status_code=303)
    return RedirectResponse(url=f"/documents?review_temp_id={session.id}", status_code=303)


@router.post("/documents/temp/{session_id}/review")
async def update_temp_document_review_form(
    session_id: str,
    document_type: str | None = Form(default=None),
    supplier_guess: str | None = Form(default=None),
    reference_number_guess: str | None = Form(default=None),
    document_date_guess: str | None = Form(default=None),
    total_amount_guess: str | None = Form(default=None),
    currency_guess: str | None = Form(default=None),
    parser_notes: str | None = Form(default=None),
):
    update_temp_document_session(
        session_id=session_id,
        document_type=document_type,
        supplier_guess=supplier_guess,
        reference_number_guess=reference_number_guess,
        document_date_guess=document_date_guess,
        total_amount_guess=total_amount_guess,
        currency_guess=currency_guess,
        parser_notes=parser_notes,
    )
    return RedirectResponse(url=f"/documents?review_temp_id={session_id}", status_code=303)


@router.post("/documents/temp/{session_id}/create-expense")
async def create_expense_from_temp_document_form(
    session_id: str,
    category_code: str = Form(...),
    expense_date: date | None = Form(default=None),
    supplier_name: str | None = Form(default=None),
    description: str | None = Form(default=None),
    amount_gbp: Decimal | None = Form(default=None),
    is_pre_trading: bool = Form(default=False),
    incurred_before_incorporation: bool = Form(default=False),
    cost_treatment: str = Form(default="revenue"),
    use_type: str = Form(default="business_only"),
    business_use_percent: Decimal | None = Form(default=None),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    expense = create_expense_from_temp_document(
        db,
        session_id=session_id,
        category_code=category_code,
        description=description,
        supplier_name=supplier_name,
        expense_date=expense_date,
        amount_gbp=amount_gbp,
        is_pre_trading=is_pre_trading,
        incurred_before_incorporation=incurred_before_incorporation,
        cost_treatment=cost_treatment,
        use_type=use_type,
        business_use_percent=business_use_percent,
        notes=notes,
    )
    return RedirectResponse(url=f"/expenses?prefill_expense_id={expense.id}", status_code=303)


@router.post("/documents/temp/{session_id}/discard")
async def discard_temp_document_form(session_id: str):
    discard_temp_document_session(session_id)
    return RedirectResponse(url="/documents", status_code=303)


@router.post("/documents/temp/{session_id}/holding")
async def save_document_to_holding_form(
    session_id: str,
    db: Session = Depends(get_db),
):
    document = save_temp_document_to_holding(db, session_id)
    return RedirectResponse(url=f"/documents?review_document_id={document.id}", status_code=303)


@router.post("/documents/{document_id}/create-expense")
async def create_expense_from_document_form(
    document_id: int,
    category_code: str = Form(...),
    expense_date: date | None = Form(default=None),
    supplier_name: str | None = Form(default=None),
    description: str | None = Form(default=None),
    amount_gbp: Decimal | None = Form(default=None),
    is_pre_trading: bool = Form(default=False),
    incurred_before_incorporation: bool = Form(default=False),
    cost_treatment: str = Form(default="revenue"),
    use_type: str = Form(default="business_only"),
    business_use_percent: Decimal | None = Form(default=None),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    expense = create_expense_from_incoming_document(
        db,
        document_id=document_id,
        category_code=category_code,
        description=description,
        supplier_name=supplier_name,
        expense_date=expense_date,
        amount_gbp=amount_gbp,
        is_pre_trading=is_pre_trading,
        incurred_before_incorporation=incurred_before_incorporation,
        cost_treatment=cost_treatment,
        use_type=use_type,
        business_use_percent=business_use_percent,
        notes=notes,
    )
    return RedirectResponse(url=f"/expenses?prefill_expense_id={expense.id}", status_code=303)


@router.post("/documents/{document_id}/review")
async def update_document_review_form(
    document_id: int,
    document_type: str | None = Form(default=None),
    supplier_guess: str | None = Form(default=None),
    reference_number_guess: str | None = Form(default=None),
    document_date_guess: str | None = Form(default=None),
    total_amount_guess: str | None = Form(default=None),
    currency_guess: str | None = Form(default=None),
    parser_notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    update_incoming_document_review(
        db,
        document_id=document_id,
        document_type=document_type,
        supplier_guess=supplier_guess,
        reference_number_guess=reference_number_guess,
        document_date_guess=document_date_guess,
        total_amount_guess=total_amount_guess,
        currency_guess=currency_guess,
        parser_notes=parser_notes,
    )
    return RedirectResponse(url=f"/documents?review_document_id={document_id}", status_code=303)


@router.post("/documents/{document_id}/discard")
async def discard_document_form(
    document_id: int,
    db: Session = Depends(get_db),
):
    try:
        discard_incoming_document(db, document_id)
    except ValueError:
        return RedirectResponse(url=f"/documents?review_document_id={document_id}", status_code=303)
    return RedirectResponse(url="/documents", status_code=303)


@router.get("/exports/expenses.csv")
def download_expenses_csv(db: Session = Depends(get_db)) -> FileResponse:
    export_path = export_expenses_csv(db)
    return FileResponse(export_path, media_type="text/csv", filename=export_path.name)


@router.get("/exports/director-loan.csv")
def download_director_loan_csv(db: Session = Depends(get_db)) -> FileResponse:
    export_path = export_director_loan_csv(db)
    return FileResponse(export_path, media_type="text/csv", filename=export_path.name)


@router.get("/exports/backup.json")
def download_backup_json(db: Session = Depends(get_db)) -> FileResponse:
    export_path = export_backup_json(db)
    return FileResponse(export_path, media_type="application/json", filename=export_path.name)


@router.get("/storage/{path:path}")
def serve_storage_file(path: str) -> FileResponse:
    target = settings.project_root / "storage" / path
    return FileResponse(target)
