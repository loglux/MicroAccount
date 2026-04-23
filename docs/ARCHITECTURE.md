# Architecture

## Architectural stance

The system should be `modular`, `UK-first`, and `local-first`.

The growth strategy is:

- start with a server-rendered local web application
- keep backend boundaries clean
- add richer APIs and storage later if justified
- avoid committing too early to a separate frontend application
- reserve a dedicated document-processing module for OCR and extraction

## Layered structure

```text
app/
  main.py
  config.py
  db/
    base.py
    session.py
  domain/
    models/
    services/
    policies/
    value_objects/
  repositories/
  documents/
    ingest.py
    extract.py
    ocr.py
    parse.py
    schemas.py
  web/
    routes/
    forms/
    templates/
  storage/
    files.py
  exports/
    csv.py
    json_backup.py
  api/
    routes/
```

## Responsibilities

### `domain/models`
Pure business entities and database models.

Initial entities:

- `Expense`
- `DirectorLoanEntry`
- `Attachment`
- `DocumentExtraction`
- `Category`
- `Supplier` later if needed

### `domain/services`
Business workflows.

Examples:

- create expense paid personally
- auto-create DLA entry
- record repayment
- calculate DLA balance
- derive repayment status if needed

### `domain/policies`
Jurisdiction-specific rules.

Initial policy module:

- `uk.py`

Responsibilities:

- rules for director-paid business expenses
- pre-trading flag behaviour
- DLA semantics
- VAT-disabled behaviour in v1

### `documents`
Document ingestion and extraction pipeline.

Responsibilities:

- create processing tasks from attachments
- choose text extraction or OCR path
- retain extracted text
- derive structured guesses for supplier, date, amount, and invoice number
- support later review workflows

### `repositories`
Database queries and persistence coordination.

Keep business rules out of repositories.

### `web/routes`
Server-rendered user interface.

This should be a thin layer that delegates to services.

### `api/routes`
Programmatic endpoints.

Even if v1 uses the web UI primarily, the backend should expose a coherent API shape to support later UI evolution.

### `storage`
Attachment persistence.

Responsibilities:

- safe filenames
- folder structure
- hash calculation
- metadata collection

### `exports`
Structured data handoff.

Initial exporters:

- expenses CSV
- DLA CSV
- JSON backup bundle

## Why not a separate frontend now

A separate frontend is not forbidden. It is deferred.

Current product needs:

- forms
- tables
- filters
- file upload
- dashboard summaries
- document-processing review later

These do not justify early SPA complexity. Flexibility should be created in the backend and service boundaries first.

## Planned growth path

### v1

- FastAPI app
- server-rendered UI
- SQLite
- local attachments
- exports
- document-processing extension points only

### v2

- Postgres option
- auth
- audit events
- richer JSON API
- PDF text extraction
- document review workflow

### v3

- OCR for scanned receipts and invoices
- optional separate frontend
- multi-user support
- accountant workspace
- advanced reporting and reconciliation
