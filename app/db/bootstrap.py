from __future__ import annotations

from sqlalchemy import Engine, inspect, text


def ensure_sqlite_schema_compatibility(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "expenses" in tables:
            expense_columns = {column["name"] for column in inspector.get_columns("expenses")}
            if "incurred_before_incorporation" not in expense_columns:
                connection.execute(
                    text(
                        "ALTER TABLE expenses "
                        "ADD COLUMN incurred_before_incorporation BOOLEAN DEFAULT 0"
                    )
                )
            if "cost_treatment" not in expense_columns:
                connection.execute(
                    text(
                        "ALTER TABLE expenses "
                        "ADD COLUMN cost_treatment VARCHAR(50) DEFAULT 'revenue'"
                    )
                )
            if "use_type" not in expense_columns:
                connection.execute(
                    text(
                        "ALTER TABLE expenses "
                        "ADD COLUMN use_type VARCHAR(50) DEFAULT 'business_only'"
                    )
                )
            if "business_use_percent" not in expense_columns:
                connection.execute(
                    text("ALTER TABLE expenses ADD COLUMN business_use_percent NUMERIC(5, 2)")
                )
            if "needs_review" not in expense_columns:
                connection.execute(
                    text("ALTER TABLE expenses ADD COLUMN needs_review BOOLEAN DEFAULT 0")
                )

        if "account_mappings" not in tables:
            connection.execute(
                text(
                    "CREATE TABLE account_mappings ("
                    "id INTEGER PRIMARY KEY, "
                    "category_code VARCHAR(100) UNIQUE, "
                    "account_code VARCHAR(20), "
                    "account_name VARCHAR(150), "
                    "created_at DATETIME, "
                    "updated_at DATETIME)"
                )
            )

        if "attachments" in tables:
            attachment_columns = {column["name"] for column in inspector.get_columns("attachments")}
            if "document_role" not in attachment_columns:
                connection.execute(
                    text(
                        "ALTER TABLE attachments "
                        "ADD COLUMN document_role VARCHAR(50) DEFAULT 'supporting_document'"
                    )
                )
            if "processing_status" not in attachment_columns:
                connection.execute(
                    text(
                        "ALTER TABLE attachments "
                        "ADD COLUMN processing_status VARCHAR(50) DEFAULT 'queued'"
                    )
                )
            if "processing_error" not in attachment_columns:
                connection.execute(text("ALTER TABLE attachments ADD COLUMN processing_error TEXT"))
