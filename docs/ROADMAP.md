# Roadmap

## Phase 0: Foundation

- define UK-first product scope
- define architecture and domain boundaries
- document accounting assumptions
- pin current framework versions
- create Makefile and quality workflow
- define containerized runtime shape

## Phase 1: Core registers

- SQLite schema
- expense register
- automatic DLA entry creation
- repayment recording
- attachment storage
- search and filtering
- CSV export
- JSON backup export
- Docker deployment
- document-processing schema extension points
- document temporary review flow
- holding area

## Phase 1.5: Product consolidation

- make `Expenses` the primary home workflow
- simplify `Documents` into a true inbox and review surface
- keep `DLA` as a focused money-ledger screen
- remove dashboard-first UX assumptions
- add supplier and category operational rules
- improve regression coverage around the main operational screens

## Phase 2: Startup finance operations

- validation improvements
- audit events
- import tooling
- backup and restore workflow
- better reporting filters
- supplier and category management
- minimal income register
- regression coverage for core workflows
- reverse proxy and auth hardening plan
- PDF text extraction and document review queue

## Phase 3: Growth path

- OCR for scanned receipts and invoices
- parsed field prefill into expense workflows
- bank CSV import and reconciliation
- Postgres support
- authentication
- role model for accountant access
- richer API surface
- optional dedicated frontend

## Non-goals until explicitly approved

- VAT engine
- payroll
- corporation tax filing automation
- full general ledger
- bank integrations with third-party providers
- autonomous no-review OCR posting into final accounts
