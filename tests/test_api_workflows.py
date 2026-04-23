from __future__ import annotations

import os
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse

TEST_ROOT = Path(__file__).resolve().parent / ".runtime"
shutil.rmtree(TEST_ROOT, ignore_errors=True)
TEST_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["LOGLUX_DATA_DIR"] = str(TEST_ROOT / "data")
os.environ["LOGLUX_STORAGE_DIR"] = str(TEST_ROOT / "storage")
os.environ["LOGLUX_EXPORT_DIR"] = str(TEST_ROOT / "exports")
os.environ["LOGLUX_DATABASE_URL"] = f"sqlite:///{TEST_ROOT / 'test.db'}"
os.environ["LOGLUX_APP_NAME"] = "MicroAccount"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


def reset_runtime_state() -> None:
    shutil.rmtree(TEST_ROOT / "exports", ignore_errors=True)
    shutil.rmtree(TEST_ROOT / "storage", ignore_errors=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_expense_creates_dla_entry_and_summary_updates() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        expense_response = client.post(
            "/api/expenses",
            json={
                "expense_date": "2026-04-23",
                "supplier_name": "Hetzner",
                "description": "Cloud server for Loglux platform",
                "amount_gbp": "29.99",
                "category_code": "hosting_and_infrastructure",
                "is_pre_trading": True,
            },
        )
        assert expense_response.status_code == 201

        loan_response = client.get("/api/director-loan")
        assert loan_response.status_code == 200
        entries = loan_response.json()
        assert len(entries) == 1
        assert entries[0]["direction"] == "loan_to_company"
        assert entries[0]["amount_gbp"] == "29.99"
        assert entries[0]["running_balance"] == "29.99"

        summary_response = client.get("/api/summary")
        assert summary_response.status_code == 200
        summary_payload = summary_response.json()
        assert summary_payload["balance_due_to_director"] == "29.99"
        assert summary_payload["expense_count"] == 1
        assert summary_payload["pre_trading_expense_count"] == 1


def test_repayment_reduces_balance_and_exports_refresh() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        client.post(
            "/api/expenses",
            json={
                "expense_date": "2026-04-23",
                "supplier_name": "Hetzner",
                "description": "Cloud server for Loglux platform",
                "amount_gbp": "29.99",
                "category_code": "hosting_and_infrastructure",
                "is_pre_trading": True,
            },
        )

        repayment_response = client.post(
            "/api/repayments",
            json={
                "entry_date": "2026-04-24",
                "amount_gbp": "9.99",
                "reference": "Bank transfer to director",
            },
        )
        assert repayment_response.status_code == 201

        summary_response = client.get("/api/summary")
        assert summary_response.status_code == 200
        assert summary_response.json()["balance_due_to_director"] == "20.00"

        ledger_response = client.get("/api/director-loan")
        assert ledger_response.status_code == 200
        rows = ledger_response.json()
        assert rows[0]["running_balance"] == "20.00"
        assert rows[1]["running_balance"] == "29.99"

        export_response = client.post("/api/exports/refresh")
        assert export_response.status_code == 200

        assert (TEST_ROOT / "exports" / "expenses.csv").exists()
        assert (TEST_ROOT / "exports" / "director-loan.csv").exists()
        assert (TEST_ROOT / "exports" / "backup.json").exists()


def test_search_filters_expenses_and_ledger() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        client.post(
            "/api/expenses",
            json={
                "expense_date": "2026-04-20",
                "supplier_name": "OpenAI",
                "description": "API credits",
                "amount_gbp": "15.00",
                "category_code": "software_subscriptions",
                "notes": "LLM testing",
            },
        )
        client.post(
            "/api/expenses",
            json={
                "expense_date": "2026-04-21",
                "supplier_name": "Namecheap",
                "description": "Domain renewal",
                "amount_gbp": "10.00",
                "category_code": "domains_and_dns",
            },
        )

        expense_search = client.get("/api/expenses", params={"search_text": "OpenAI"})
        assert expense_search.status_code == 200
        assert len(expense_search.json()) == 1
        assert expense_search.json()[0]["supplier_name"] == "OpenAI"

        ledger_search = client.get("/api/director-loan", params={"search_text": "Domain"})
        assert ledger_search.status_code == 200
        assert len(ledger_search.json()) == 1
        assert "Domain renewal" in ledger_search.json()[0]["reference"]


def test_attachment_prefill_returns_empty_for_missing_attachment() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        response = client.get("/api/attachments/999/prefill")
        assert response.status_code == 200
        assert response.json() == {}


def test_expense_prefill_returns_empty_when_no_attachments_exist() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        create_response = client.post(
            "/api/expenses",
            json={
                "expense_date": "2026-04-23",
                "supplier_name": "Anthropic",
                "description": "Claude subscription",
                "amount_gbp": "20.00",
                "category_code": "software_subscriptions",
            },
        )
        assert create_response.status_code == 201

        response = client.get(f"/api/expenses/{create_response.json()['id']}/prefill")
        assert response.status_code == 200
        assert response.json() == {}


def test_document_first_upload_and_create_expense_flow() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        upload_response = client.post(
            "/api/incoming-documents/upload",
            files={"documents": ("note.txt", b"Anthropic invoice placeholder", "text/plain")},
        )
        assert upload_response.status_code == 201
        uploaded = upload_response.json()
        assert len(uploaded) == 1
        document_id = uploaded[0]["id"]

        document_response = client.get(f"/api/incoming-documents/{document_id}")
        assert document_response.status_code == 200
        assert document_response.json()["original_filename"] == "note.txt"

        review_response = client.post(
            f"/api/incoming-documents/{document_id}/review",
            json={
                "document_type": "invoice",
                "supplier_guess": "Anthropic",
                "reference_number_guess": "TEST-001",
                "document_date_guess": "2026-04-06",
                "total_amount_guess": "£18.00",
                "currency_guess": "GBP",
            },
        )
        assert review_response.status_code == 200

        create_expense_response = client.post(
            f"/api/incoming-documents/{document_id}/create-expense",
            json={
                "category_code": "software_subscriptions",
                "description": "Imported from staged document",
            },
        )
        assert create_expense_response.status_code == 201
        expense_id = create_expense_response.json()["expense_id"]

        expenses_response = client.get("/api/expenses")
        assert expenses_response.status_code == 200
        assert any(item["id"] == expense_id for item in expenses_response.json())

        staged_document_response = client.get(f"/api/incoming-documents/{document_id}")
        assert staged_document_response.status_code == 200
        assert staged_document_response.json()["linked_expense_id"] == expense_id


def test_incoming_document_can_be_discarded_before_linking() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        upload_response = client.post(
            "/api/incoming-documents/upload",
            files={"documents": ("mistake.txt", b"wrong upload", "text/plain")},
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()[0]["id"]

        document_response = client.get(f"/api/incoming-documents/{document_id}")
        assert document_response.status_code == 200
        storage_files = list((TEST_ROOT / "storage").rglob("*"))
        assert any(path.is_file() for path in storage_files)

        discard_response = client.delete(f"/api/incoming-documents/{document_id}")
        assert discard_response.status_code == 204

        missing_response = client.get(f"/api/incoming-documents/{document_id}")
        assert missing_response.status_code == 200
        assert missing_response.json() == {}
        assert not any(path.is_file() for path in (TEST_ROOT / "storage").rglob("*"))


def test_temp_document_review_stays_out_of_db_until_confirmed() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        upload_response = client.post(
            "/documents/upload",
            files={"documents": ("draft.txt", b"temporary parse only", "text/plain")},
            follow_redirects=False,
        )
        assert upload_response.status_code == 303
        session_id = parse_qs(urlparse(upload_response.headers["location"]).query)[
            "review_temp_id"
        ][0]

        session_file = TEST_ROOT / "data" / "temp_sessions" / f"{session_id}.json"
        assert session_file.exists()

        incoming_documents_response = client.get("/api/incoming-documents")
        assert incoming_documents_response.status_code == 200
        assert incoming_documents_response.json() == []

        review_response = client.post(
            f"/documents/temp/{session_id}/review",
            data={
                "document_type": "invoice",
                "supplier_guess": "IONOS",
                "reference_number_guess": "IONOS-001",
                "document_date_guess": "2026-04-08",
                "total_amount_guess": "£6.00",
                "currency_guess": "GBP",
            },
            follow_redirects=False,
        )
        assert review_response.status_code == 303

        create_response = client.post(
            f"/documents/temp/{session_id}/create-expense",
            data={
                "category_code": "hosting_and_infrastructure",
                "description": "Imported from temporary review",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303
        assert not session_file.exists()

        expenses_response = client.get("/api/expenses")
        assert expenses_response.status_code == 200
        assert len(expenses_response.json()) == 1
