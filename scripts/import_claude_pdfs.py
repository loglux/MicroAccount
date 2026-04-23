from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.config import ensure_directories
from app.db.base import Base
from app.db.bootstrap import ensure_sqlite_schema_compatibility
from app.db.session import SessionLocal, engine
from app.services.accounting import (
    ExpenseInput,
    attach_files_to_expense,
    create_expense,
    get_attachment_prefill,
    get_expense_prefill_from_primary_attachment,
)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    invoice_path = project_root / "Invoice-6Y5GUSBL-0059.pdf"
    receipt_path = project_root / "Receipt-2546-3344-2896.pdf"

    missing = [str(path) for path in (invoice_path, receipt_path) if not path.exists()]
    if missing:
        raise SystemExit(f"Missing files: {', '.join(missing)}")

    ensure_directories()
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema_compatibility(engine)

    with SessionLocal() as db:
        expense = create_expense(
            db,
            ExpenseInput(
                expense_date=date(2026, 4, 6),
                supplier_name="Anthropic",
                description="Claude subscription imported from uploaded PDF documents",
                amount_gbp=Decimal("18.00"),
                category_code="software_subscriptions",
                notes="Created from local Claude invoice + receipt document import.",
            ),
            uploads=[],
        )
        attachments = attach_files_to_expense(db, expense.id, [invoice_path, receipt_path])
        prefill = get_expense_prefill_from_primary_attachment(db, expense.id)

        output = {
            "expense_id": expense.id,
            "attachments": [
                {
                    "attachment_id": attachment.id,
                    "filename": attachment.original_filename,
                    "document_role": attachment.document_role,
                    "processing_status": attachment.processing_status,
                    "prefill": get_attachment_prefill(db, attachment.id),
                }
                for attachment in attachments
            ],
            "primary_prefill": prefill,
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
