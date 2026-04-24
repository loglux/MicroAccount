# Implementation Plan

## Purpose

This document is the `single execution plan` for the current product phase.

It exists so the team does not need to reconstruct the plan from:

- chat history
- memory
- partial docs
- current code shape

It should answer:

- what already exists
- what the target product shape is
- which fields belong where
- what order to build in
- what counts as done

## Current state

The repository already contains:

- FastAPI application
- SQLite-first persistence
- expense register
- Director's Loan Account ledger
- repayment workflow
- attachment storage
- temporary document review sessions
- holding area
- PDF text extraction foundation
- CSV and JSON exports
- Docker runtime
- linting, tests, and Makefile workflow

The repository does **not** yet have a finished product UI model.

The biggest current gap is not backend capability but `workflow coherence`.

## Target product shape

The target near-term product shape is:

1. `Expenses`
   Main working surface and default home flow.
2. `Documents`
   Inbox and review workflow for uploaded files.
3. `DLA`
   Money ledger for director funding and repayments.
4. `Income`
   Minimal separate register added after the core three screens are stable.
5. `Settings`
   Categories, mappings, and supplier rules after the core workflows are stable.

## Product rules

- `Expense` is the primary object for current v1 work.
- `Document` is a source and evidence object.
- `DirectorLoanEntry` is the money consequence of an expense or repayment.
- `Holding area` is optional and explicit, not the default destination of every file.
- `Income` must be added as a separate register later, not folded awkwardly into expenses.

## Screen-by-screen plan

### 1. Expenses

This becomes the main home screen.

#### Purpose

- see all recorded company expenses
- add an expense manually
- inspect category and review status
- access linked documents
- jump into document-first intake when needed

#### Primary object

- `Expense`

#### Primary action

- `Add expense`

#### Secondary action

- `Create from document`

#### Required fields in manual form

- `expense_date` required
- `amount_gbp` required
- `category_code` required
- `supplier_name` optional
- `description` required
- `notes` optional
- `attachments` optional, multiple

#### UK review fields

- `is_pre_trading`
- `incurred_before_incorporation`
- `cost_treatment`
- `use_type`
- `business_use_percent`

#### Register columns

- date
- supplier
- description
- category
- amount
- review status
- documents

#### Derived status indicators

- `pre-trading`
- `before incorporation`
- `formation/capital`
- `mixed use`
- `needs review`

### 2. Documents

This becomes a dedicated review workspace.

#### Purpose

- upload one file
- review extracted fields
- correct metadata
- create an expense from the file
- hold a file for later
- delete a temporary file without trace

#### Primary object

- `incoming document under review`

#### Primary action

- `Create expense from document`

#### Upload fields

- one file input

#### Review fields

- `document_type`
- `supplier_guess`
- `reference_number_guess`
- `document_date_guess`
- `total_amount_guess`
- `currency_guess`
- `parser_notes`

#### Create-expense-from-document fields

- `category_code` required
- `expense_date`
- `amount_gbp`
- `supplier_name`
- `description`
- `notes`
- UK review fields:
  - `is_pre_trading`
  - `incurred_before_incorporation`
  - `cost_treatment`
  - `use_type`
  - `business_use_percent`

#### Holding area columns

- filename
- type
- supplier
- amount
- action link to review

### 3. DLA

This stays narrow and operational.

#### Purpose

- inspect running DLA balance
- record repayments
- review money movement history

#### Primary object

- `DirectorLoanEntry`

#### Primary action

- `Record repayment`

#### Repayment fields

- `entry_date` required
- `amount_gbp` required
- `reference` required
- `notes` optional

#### Ledger columns

- date
- direction
- amount
- running balance
- reference
- notes

### 4. Income

This is not part of the current main implementation wave, but it is approved as the next domain expansion.

#### Purpose

- record money received by the company
- keep a simple early revenue register

#### Planned fields

- `income_date` required
- `source_name` required
- `description` required
- `amount_gbp` required
- `reference` optional
- `notes` optional
- `attachments` optional later

#### Planned table columns

- date
- source
- description
- amount
- reference
- notes

### 5. Settings

This is an admin and rules screen, not a daily workflow.

#### Purpose

- manage categories
- manage category to account mapping
- manage supplier rules
- define company defaults later

#### Planned entities

- `Category`
- `AccountMapping`
- `SupplierRule`

## Data model status

### Already implemented

- `Expense`
- `DirectorLoanEntry`
- `Attachment`
- `DocumentExtraction`
- temporary document session model outside main DB
- account mapping seed layer

### Planned next additions

- `IncomeRecord`
- `SupplierRule`
- richer category management
- bank transaction layer later

## Route plan

### Current routes already present

- `/`
- `/expenses`
- `/documents`
- `/dla`
- expense create routes
- repayment create routes
- document upload/review/create routes

### Intended route evolution

#### Near term

- make `/` redirect to `/expenses`
- keep `/documents`
- keep `/dla`

#### Next

- add `/income`
- add `/settings`

## Build order

### Stage 1: Product reset

1. make `Expenses` the default home workflow
2. reduce or remove dashboard-first entry
3. stop treating overview as the main product surface

### Stage 2: Expense screen cleanup

1. keep the expense table primary
2. keep manual add in a controlled side rail
3. ensure document links and statuses are easy to scan

### Stage 3: Documents screen cleanup

1. make upload and review the main focus
2. stop mixing multiple equal-weight subflows
3. keep holding area secondary

### Stage 4: DLA cleanup

1. keep DLA focused on money movement only
2. keep repayment entry simple
3. improve clarity, not breadth

### Stage 5: Income module (done)

1. add `IncomeRecord` model — done
2. add `/income` (GET + POST) — done
3. keep the feature deliberately minimal — no attachments, no categories, no DLA coupling

### Stage 6: Settings and rules

1. add editable categories
2. add supplier-to-category mapping
3. add account mapping management

## Definition of done by stage

### Product reset done

- `/expenses` is the clear main surface
- `/` no longer behaves like a fake dashboard-first homepage
- navigation reflects the real operational model

### Expense screen done

- manual expense creation is clear
- expense register is easy to scan
- UK review flags are visible and understandable
- document evidence is reachable without confusion

### Documents screen done

- upload is obvious
- one document can be reviewed at a time
- extracted fields can be corrected
- creating an expense is the dominant action
- holding and delete remain secondary

### DLA screen done

- repayment entry is clear
- ledger is readable
- balance semantics are understandable

### Income screen done

- a simple income record can be created
- income is visible in its own register
- no accidental bookkeeping-suite scope is introduced

## Engineering checklist for each stage

- update relevant templates
- update relevant services if workflow changes
- update tests
- update `docs/V1_BLUEPRINT.md` if fields or routes change
- update `docs/IA_UX_BLUEPRINT.md` if screen responsibilities change
- update `docs/PRODUCT_CONCEPT.md` if product scope changes
- run `make check`
- rebuild Docker if UI or runtime behaviour changed

## Immediate next step

The next implementation step should be:

- treat `Expenses` as the true home workflow
- simplify `Documents` into a clearer review surface
- stop investing in an overview-first UX
