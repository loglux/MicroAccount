from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.services.income import get_income_summary, list_income_records
from tests.test_api_workflows import reset_runtime_state


def test_income_form_creates_record_and_updates_summary() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        response = client.post(
            "/income",
            data={
                "income_date": "2026-04-22",
                "source_name": "Acme Ltd",
                "description": "Consulting — March engagement",
                "amount_gbp": "1500.00",
                "reference": "INV-0001",
                "notes": "Paid by bank transfer",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/income"

    with SessionLocal() as db:
        records = list_income_records(db)
        assert len(records) == 1
        record = records[0]
        assert record.source_name == "Acme Ltd"
        assert record.description == "Consulting — March engagement"
        assert str(record.amount_gbp) == "1500.00"
        assert record.reference == "INV-0001"

        summary = get_income_summary(db)
        assert str(summary.total_received) == "1500.00"
        assert summary.record_count == 1


def test_income_page_renders_and_lists_records() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        client.post(
            "/income",
            data={
                "income_date": "2026-04-20",
                "source_name": "Contoso",
                "description": "Retainer",
                "amount_gbp": "500.00",
            },
            follow_redirects=False,
        )

        page = client.get("/income")
        assert page.status_code == 200
        body = page.text
        assert "Contoso" in body
        assert "Retainer" in body
        assert "£500.00" in body
        assert "Income register" in body


def test_income_search_filters_records() -> None:
    reset_runtime_state()
    with TestClient(app) as client:
        for source, description, amount in [
            ("Acme Ltd", "Consulting", "1000.00"),
            ("Contoso", "Retainer", "500.00"),
        ]:
            client.post(
                "/income",
                data={
                    "income_date": "2026-04-01",
                    "source_name": source,
                    "description": description,
                    "amount_gbp": amount,
                },
                follow_redirects=False,
            )

        filtered = client.get("/income", params={"search_text": "Acme"})
        assert "Acme Ltd" in filtered.text
        assert "Contoso" not in filtered.text
