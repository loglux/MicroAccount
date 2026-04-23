# AGENTS.md

## Purpose

This repository builds a focused accounting tool for `Loglux Ltd`, a UK limited company.

The product is not a generic finance app. It is a `UK-first local accounting workflow` for a sole director who pays company expenses personally and needs a clean Director's Loan Account record.

## Product boundaries

Contributors must optimise for:

- clarity of records
- low operational complexity
- future accountant handoff
- local or self-hosted deployment
- modular backend growth

Contributors must avoid turning the v1 product into:

- a full bookkeeping suite
- a generic international accounting platform
- a subscription-style SaaS clone
- a frontend-heavy architecture without a concrete need

## Domain assumptions

Assume the following unless documentation is explicitly changed:

- jurisdiction is `United Kingdom`
- entity is a `private limited company`
- there is currently `one director`
- many expenses are paid using the director's personal card
- those expenses should create `loan_to_company` entries in the DLA ledger
- repayments from company to director should create `repayment_to_director` entries
- VAT is not enabled in v1

## Engineering rules

- Keep backend logic modular and testable.
- Keep UK-specific policy logic explicit and isolated.
- Prefer server-rendered UI for v1 unless requirements materially change.
- Avoid premature complexity in the frontend stack.
- Design SQLite-first, but do not hard-code the app so tightly that Postgres migration becomes painful.
- Preserve a clean separation between domain models, business services, repositories, web/UI, and export logic.

## Required documentation discipline

When changing behaviour, update the relevant docs:

- `README.md` for project-level intent or setup changes
- `docs/UK_RULES.md` for UK accounting assumptions or business rules
- `docs/V1_BLUEPRINT.md` for workflow, field, and API changes
- `docs/ARCHITECTURE.md` for structural or module-boundary changes
- `docs/ROADMAP.md` when priorities or delivery phases shift
- `docs/TOOLING.md` when commands or quality processes change

## Coding expectations

- Use clear names that match UK accounting concepts.
- Prefer `Expense`, `DirectorLoanEntry`, `Repayment`, and `Attachment` over abstract generic names.
- Avoid hardcoding logic into route handlers.
- Keep export formats stable once introduced.
- Make file storage paths deterministic and safe.
- Treat accountant handoff as a first-class use case.

## UX expectations

The interface should be understandable to a director who has never used accounting software.

Use language like:

- `Business expense paid personally`
- `Director loan to company`
- `Repayment to director`
- `Company owes director`

Avoid jargon-heavy ERP vocabulary unless there is a strong reason.
