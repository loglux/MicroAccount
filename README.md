# MicroAccount

UK-first lightweight accounting tool for `Loglux Ltd`.

The project is designed for a very specific early-stage scenario:

- UK limited company
- one director
- no VAT registration yet
- no income yet or very early trading
- business expenses often paid personally by the director
- need to maintain a clean Director's Loan Account (DLA)
- need to keep invoice files organised locally

This is not a full commercial accounting platform. It is a focused internal tool that captures the records your accountant will need later.

## Project intent

The tool should make it easy to:

- record business expenses paid with a personal card
- classify those payments as money the director lent to the company
- record repayments from the company back to the director
- calculate the running DLA balance
- store invoice attachments locally
- review documents before they become permanent records
- prepare uploaded PDFs and receipts for later extraction and OCR workflows
- discard mistakenly uploaded staged documents before they are linked to an expense
- review uploaded documents in a temporary session before committing them
- optionally move selected documents into a separate holding area for later import
- grow into simple income tracking later
- export structured data later to external accounting software if needed

When multiple files are attached to one expense, the first file is treated as the primary document for prefill and the rest are supporting documents by default.

For document-first intake, the default upload flow is now temporary:

- upload a document into a temporary review session
- inspect and edit extracted fields
- either `Create expense`, `Save to holding area`, or `Delete temporary document`
- only confirmed or intentionally held documents are persisted

## Core principles

- `UK-first`: terminology and workflows should reflect UK limited company reality
- `pragmatic`: solve the actual operating problem before trying to become accounting software
- `modular`: keep the backend clean enough to grow into a more capable system later
- `local-first`: SQLite and local file storage are first-class, not second-rate fallbacks
- `container-ready`: Docker is a first-class runtime, not an afterthought
- `accountant-friendly`: exports and records should be easy for a future accountant to inspect

## Planned v1 scope

- expense capture
- automatic DLA entries for director-funded expenses
- repayment recording
- invoice attachments
- filterable expense and DLA views
- document intake and review flow
- CSV export
- JSON backup export
- Docker-based deployment
- document-processing extension points for PDF and receipt recognition

## Product shape

The product should be understood as a small set of operational registers:

- `Expenses`
- `Documents`
- `Money` through the DLA ledger and repayments
- `Income` later

`Expenses` is the primary home workflow. Documents assist expense creation and evidence collection. DLA records the money consequences of those expenses. Later, income should be recorded in its own simple register instead of being forced into the expense model.

## Out of scope for v1

- VAT
- payroll
- bank feeds
- full double-entry ledger
- debtor/creditor workflows
- multi-user permissions
- advanced reporting
- multi-currency accounting
- production OCR pipeline

## Proposed stack

- Python `3.14.4`
- FastAPI `0.135.3`
- SQLAlchemy `2.0.49`
- Uvicorn `0.43.0`
- Jinja2 `3.1.6`
- Pydantic `2.13.3`
- python-multipart `0.0.26`
- SQLite for local persistence
- Docker and Compose for deployment

## Local Python workflow

```bash
make dev-install
make run
```

Then open `http://127.0.0.1:8000`.

## Docker workflow

Default host port is `8040`, chosen because it is currently free on this machine.

```bash
make docker-build
make docker-up
```

Then open:

- `http://127.0.0.1:8040` on the host machine
- `http://<host-ip>:8040` from another machine on the same network

You can override the port when needed:

```bash
MICROACCOUNT_PORT=8120 make docker-up
```

## Persistence

Docker mounts these host directories:

- `./data`
- `./storage`
- `./exports`

That means the SQLite database, uploaded invoice files, and generated exports stay on the host and survive rebuilds and container replacement.

## Tooling

The repository standardises these workflows:

- `make install`
- `make run`
- `make fmt`
- `make lint`
- `make test`
- `make check`
- `make docker-build`
- `make docker-up`
- `make docker-down`

## Documentation map

- `AGENTS.md`: working rules for contributors and AI agents
- `docs/ARCHITECTURE.md`: system boundaries and module layout
- `docs/PRODUCT_CONCEPT.md`: product definition, primary objects, and operating model
- `docs/IA_UX_BLUEPRINT.md`: information architecture and screen responsibilities
- `docs/ROADMAP.md`: staged delivery plan
- `docs/UK_RULES.md`: UK-specific domain assumptions and accounting rules for the app
- `docs/V1_BLUEPRINT.md`: exact first-version data model, UX, and API shape
- `docs/TOOLING.md`: project commands, testing, and quality workflow
- `docs/DEPLOYMENT.md`: Docker and browser-access deployment model
- `docs/DOCUMENT_PROCESSING.md`: OCR and PDF extraction architecture
