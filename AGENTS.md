# AGENTS.md

## Purpose

This repository builds a focused accounting tool for `Loglux Ltd`, a UK limited company.

The product is not a generic finance app. It is a `UK-first local finance operating system` for an early-stage company that needs to keep expenses, documents, repayments, and later income records in order without paying for commercial accounting software too early.

The current operating model:

- one director
- company expenses often paid personally
- clean Director's Loan Account tracking
- accountant-friendly records and exports
- document-first intake with review before commit
- optional holding area for selected documents
- a growth path toward simple income tracking

## Product boundaries

Optimise for:

- clarity of records
- low operational complexity
- future accountant handoff
- local or self-hosted deployment
- modular backend growth
- explicit workflows over feature sprawl

Do not turn v1 into:

- a full bookkeeping suite
- a generic international accounting platform
- a subscription-style SaaS clone
- a frontend-heavy architecture without a concrete need
- a dashboard-card demo instead of a working tool
- a document lab where the accounting object becomes unclear

## Domain assumptions

Assume the following unless documentation is explicitly changed:

- jurisdiction is `United Kingdom`
- entity is a `private limited company`
- there is currently `one director`
- many expenses are paid using the director's personal card
- those expenses should create `loan_to_company` entries in the DLA ledger
- repayments from company to director should create `repayment_to_director` entries
- VAT is not enabled in v1
- uploaded documents are reviewed in a temporary state before they become permanent records
- the holding area is an explicit user choice, not the default destination for every file
- future income tracking is allowed, but stays simple and separate from expense workflows unless docs change

## Product shape

Operational registers:

- `Expenses` — main working surface and home flow
- `Documents` — intake and review workflow
- `DLA` — money ledger for director funding and repayments
- `Income` — separate simple register (later)

Authoritative screen structure and navigation lives in `docs/IA_UX_BLUEPRINT.md`; field and route contract in `docs/V1_BLUEPRINT.md`. Do not duplicate those here.

Each screen has **one main job** and **one obvious primary action**. Do not build equal-weight screens.

## Engineering rules

- Backend logic is modular and testable.
- UK-specific policy logic is explicit and isolated (`app/domain/policies/`).
- Server-rendered UI for v1. Do not add frontend frameworks without a concrete need.
- SQLite-first, but not so tightly coupled that a future Postgres migration becomes painful.
- Clean separation between domain models, services, repositories, web/UI, and export logic.
- Route handlers stay thin — they parse input and delegate. Product logic lives in services.
- Prefer small, composable services over giant workflow functions.
- Keep temporary document state separate from committed accounting records.
- Do not blur `Document`, `Expense`, and `DirectorLoanEntry` into one overloaded model.

## Coding conventions

- Names match UK accounting concepts: `Expense`, `DirectorLoanEntry`, `Repayment`, `Attachment`, `IncomeRecord` (later).
- Export formats are stable once introduced.
- File storage paths are deterministic and safe.
- Accountant handoff is a first-class use case; exports and record shape reflect that.

## Quality bar

- `make check` is green before a change is considered done.
- Tests accompany any change to workflow-critical behaviour.
- No speculative abstractions without a concrete growth path.
- No UI changes that weaken the product model for short-term cosmetic gains.
- When touching an area, leave it clearer than it was before.

Tooling and test layers are documented in `docs/TOOLING.md`. Docker is a first-class runtime, not an afterthought.

## Documentation discipline

When changing behaviour, update the relevant docs:

- `README.md` — project-level intent or setup
- `docs/PRODUCT_CONCEPT.md` — product definition and operating model
- `docs/IA_UX_BLUEPRINT.md` — screen structure, navigation, UX responsibilities
- `docs/V1_BLUEPRINT.md` — workflow, field, and API contract
- `docs/ARCHITECTURE.md` — structural and module-boundary changes
- `docs/UK_RULES.md` — UK accounting assumptions and business rules
- `docs/ROADMAP.md` — priority or delivery-phase shifts
- `docs/TOOLING.md` — commands, tests, and quality process
- `docs/DOCUMENT_PROCESSING.md` — OCR and PDF extraction architecture
- `docs/DEPLOYMENT.md` — Docker and browser-access deployment

## Content rules

- No raw code identifiers in the UI. `category_code`, `document_role`, `processing_status`, and similar enum values must be mapped to human labels before rendering.
- UI language is plain English, readable by a director who has never used accounting software. No snake_case, no internal jargon on screen.
- Internal codes belong in the database, the API, and exports — never in what the user reads on a page.
- Label maps live in `app/services/labels.py` (or an equivalent single module). Templates access them through the `humanize` Jinja filter.

## UX expectations

Use language like:

- `Business expense paid personally`
- `Director loan to company`
- `Repayment to director`
- `Company owes director`

Avoid ERP jargon. If a UI change makes the product harder to understand operationally, it is a regression even if it looks cleaner.

## Visual style

The UI is a back-office operating tool, not a branded product page.

Forbidden:

- serif typography (Iowan Old Style, Palatino, Georgia) anywhere in the app
- clamp-scaled display headings (e.g. `clamp(2rem, 5vw, 4rem)`)
- radii above 6px
- box-shadows and elevation layers on workspace chrome
- `backdrop-filter`, frosted-glass effects
- decorative gradients in nav, headers, brand blocks, metric cards
- SaaS-style KPI cards in page headers
- rise-in / fade-in animations on layout elements
- emoji in the UI unless the user explicitly asks

Preferred:

- one sans-serif family everywhere (system stack or IBM Plex Sans)
- flat panels with 1px borders, radius 4–6px
- dense padding (8–14px) inside cards and table cells
- one accent colour for primary action and active nav
- tables and forms are the primary reading surface — hover highlights on rows, sticky headers, clear empty states, no compression under decorative headers
- one short H1 per page, normal weight, ≤22px
- primary action per screen is a filled accent button; secondary is a ghost button with a 1px border; destructive is a ghost in the danger colour

## Agents and skills

Use agents and skills when they materially improve quality, speed, or correctness — not as decoration.

- Good: a frontend-focused agent for a clearly scoped UI redesign, a codebase explorer for a narrow architectural question, a reusable skill for a repeated specialised workflow.
- Bad: extra agents without a clear ownership boundary, delegation that hides unclear product thinking, project-specific skills when the docs in this repo already cover the ground.

`AGENTS.md` and the `docs/` tree are the primary sources of truth. Skills are optional support, not replacements for repository documentation.
