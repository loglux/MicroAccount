from __future__ import annotations

import io
from decimal import Decimal

from fastapi.testclient import TestClient

from app.config import settings
from app.db.session import SessionLocal
from app.domain.models import Attachment, DirectorLoanEntry, DocumentExtraction, Expense
from app.domain.policies.uk import DLA_LOAN_TO_COMPANY
from app.main import app
from app.services.accounting import get_summary
from tests.test_api_workflows import reset_runtime_state


def _create_expense_via_api(client: TestClient, **overrides) -> int:
    payload = {
        "expense_date": "2026-04-10",
        "supplier_name": "Hetzner",
        "description": "VPS monthly fee",
        "amount_gbp": "45.00",
        "category_code": "hosting_and_infrastructure",
        "is_pre_trading": False,
    }
    payload.update(overrides)
    response = client.post("/api/expenses", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_editing_amount_updates_linked_dla_entry() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        expense_id = _create_expense_via_api(client, amount_gbp="45.00")

        with SessionLocal() as db:
            summary_before = get_summary(db)
            assert summary_before.total_loaned == Decimal("45.00")

        response = client.post(
            f"/expenses/{expense_id}",
            data={
                "expense_date": "2026-04-10",
                "supplier_name": "Hetzner",
                "description": "VPS monthly fee (upgraded)",
                "amount_gbp": "60.00",
                "category_code": "hosting_and_infrastructure",
                "cost_treatment": "revenue",
                "use_type": "business_only",
                "business_use_percent": "100.00",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == f"/expenses/{expense_id}"

        with SessionLocal() as db:
            expense = db.get(Expense, expense_id)
            assert expense is not None
            assert expense.amount_gbp == Decimal("60.00")
            assert expense.description == "VPS monthly fee (upgraded)"

            loan_entry = (
                db.query(DirectorLoanEntry)
                .filter(
                    DirectorLoanEntry.expense_id == expense_id,
                    DirectorLoanEntry.direction == DLA_LOAN_TO_COMPANY,
                )
                .one()
            )
            assert loan_entry.amount_gbp == Decimal("60.00")
            assert "(upgraded)" in loan_entry.reference

            summary_after = get_summary(db)
            assert summary_after.total_loaned == Decimal("60.00")


def test_deleting_expense_cascades_to_dla_and_attachments() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        expense_id = _create_expense_via_api(client, amount_gbp="45.00")

        attach_response = client.post(
            f"/expenses/{expense_id}/attachments",
            files={"attachments": ("note.txt", io.BytesIO(b"evidence"), "text/plain")},
            follow_redirects=False,
        )
        assert attach_response.status_code == 303

        with SessionLocal() as db:
            attachments = db.query(Attachment).filter(Attachment.expense_id == expense_id).all()
            assert len(attachments) == 1
            stored_file = settings.project_root / attachments[0].storage_path
            assert stored_file.exists()

        delete_response = client.post(
            f"/expenses/{expense_id}/delete", follow_redirects=False
        )
        assert delete_response.status_code == 303
        assert delete_response.headers["location"] == "/expenses"

        with SessionLocal() as db:
            assert db.get(Expense, expense_id) is None
            assert (
                db.query(DirectorLoanEntry)
                .filter(DirectorLoanEntry.expense_id == expense_id)
                .count()
                == 0
            )
            assert (
                db.query(Attachment).filter(Attachment.expense_id == expense_id).count()
                == 0
            )
            assert (
                db.query(DocumentExtraction)
                .filter(DocumentExtraction.attachment_id.in_([a.id for a in attachments]))
                .count()
                == 0
            )

            summary = get_summary(db)
            assert summary.total_loaned == Decimal("0.00")

        assert not stored_file.exists()


def test_removing_attachment_keeps_expense_but_deletes_file() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        expense_id = _create_expense_via_api(client)
        client.post(
            f"/expenses/{expense_id}/attachments",
            files={"attachments": ("note.txt", io.BytesIO(b"evidence"), "text/plain")},
            follow_redirects=False,
        )

        with SessionLocal() as db:
            attachment = (
                db.query(Attachment).filter(Attachment.expense_id == expense_id).one()
            )
            attachment_id = attachment.id
            stored_file = settings.project_root / attachment.storage_path
            assert stored_file.exists()

        remove_response = client.post(
            f"/expenses/{expense_id}/attachments/{attachment_id}/delete",
            follow_redirects=False,
        )
        assert remove_response.status_code == 303

        with SessionLocal() as db:
            assert db.get(Expense, expense_id) is not None
            assert (
                db.query(Attachment).filter(Attachment.expense_id == expense_id).count()
                == 0
            )

        assert not stored_file.exists()


def test_expense_detail_page_renders_form_with_current_values() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        expense_id = _create_expense_via_api(
            client,
            description="Something very specific",
            amount_gbp="12.34",
        )

        response = client.get(f"/expenses/{expense_id}")
        assert response.status_code == 200
        body = response.text
        assert "Something very specific" in body
        assert "12.34" in body
        assert "Edit expense" in body
        assert f'action="/expenses/{expense_id}"' in body


def test_opening_detail_for_missing_expense_redirects_to_register() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        response = client.get("/expenses/9999", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/expenses"
