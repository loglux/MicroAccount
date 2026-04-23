# V1 Blueprint

## Main user goal

The user needs a practical internal finance tool for an early-stage UK ltd:

- record company expenses
- store supporting documents
- maintain a clean running Director's Loan Account
- record repayments
- prepare for later income tracking

without using commercial accounting software.

## Primary workflows

### 1. Record expense paid personally

Fields:

- date
- supplier name
- description
- amount GBP
- category
- payment method fixed as `director_personal_card`
- expense type fixed as `director_loan_funded_expense`
- pre-trading yes or no
- notes
- one or more attachments

Result:

- create `Expense`
- create linked `DirectorLoanEntry` with `loan_to_company`
- create `Attachment` records
- create placeholder `DocumentExtraction` rows for future OCR/text processing

### 2. Record repayment to director

Fields:

- date
- amount GBP
- reference
- notes

Result:

- create `DirectorLoanEntry` with `repayment_to_director`

### 3. Stage and discard uploaded documents

Result:

- uploaded documents first enter a temporary review session outside the main database
- if the document is not confirmed, it can be deleted with no lasting record
- if the user wants to keep it for later, it can be moved into a separate holding area
- only confirmed expense creation or explicit holding-area save persists the document

### 4. Review DLA position

The DLA screen must show:

- total personally funded expenses
- total repaid to director
- current balance company owes director
- running ledger entries

### 5. Record income later

Income is not the dominant v1 workflow, but the product should leave a clean path for a simple future `IncomeRecord` register instead of locking the app into expense-only thinking.

## Data model

### `expenses`

- `id`
- `expense_date`
- `supplier_name`
- `description`
- `amount_gbp`
- `currency`
- `category_code`
- `paid_by`
- `expense_type`
- `is_pre_trading`
- `is_business_use`
- `allowable_for_ct` nullable
- `status`
- `notes`
- `created_at`
- `updated_at`

### `director_loan_entries`

- `id`
- `entry_date`
- `entry_type`
- `direction`
- `amount_gbp`
- `reference`
- `expense_id` nullable
- `notes`
- `created_at`

### `attachments`

- `id`
- `expense_id`
- `original_filename`
- `stored_filename`
- `mime_type`
- `file_size`
- `sha256`
- `storage_path`
- `document_role`
- `processing_status`
- `processing_error`
- `uploaded_at`

### `document_extractions`

- `id`
- `attachment_id`
- `extractor_name`
- `processing_status`
- `document_type`
- `extracted_text`
- `supplier_guess`
- `invoice_number_guess`
- `invoice_date_guess`
- `total_amount_guess`
- `currency_guess`
- `confidence_score`
- `parser_notes`
- `created_at`
- `updated_at`

## API surface

### Web routes

- `GET /`
- `GET /expenses`
- `POST /expenses`
- `GET /documents`
- `POST /documents/upload`
- `GET /dla`
- `POST /repayments`
- `GET /exports/expenses.csv`
- `GET /exports/director-loan.csv`
- `GET /exports/backup.json`

### JSON endpoints

- `GET /api/summary`
- `GET /api/expenses`
- `POST /api/expenses`
- `GET /api/director-loan`
- `POST /api/repayments`

## UX guidance

The app must not feel like generic accounting software and must not lead with a dashboard-first structure.

The intended IA is:

- `Expenses` as the main home workflow
- `Documents` as a separate intake and review workspace
- `DLA` as a focused money-ledger screen
- `Income` later as a minimal separate register

Use plain language:

- `Add business expense paid personally`
- `Create expense from document`
- `Record company repayment to you`
- `Company owes director`

Avoid jargon such as:

- accounts payable
- owner contribution
- payable ledger
- sub-ledger

## Home-screen stance

The product should not depend on a heavy overview page.

Preferred behaviour:

- `/` should eventually redirect to `/expenses`

Reason:

- the expense register is the dominant daily-use working surface
- overview is secondary to record creation and review

## Export requirements

### CSV

CSV is not the primary UX.

It exists for:

- accountant handoff
- migration to a larger system
- offline backup usability

### JSON backup

A structured JSON export should be included in v1 because it is more suitable than CSV for complete backup and later restoration.

## Document processing stance

OCR and PDF extraction are planned as assistive workflows.

Extracted document data should not automatically become final accounting entries without review.

If both an invoice and a receipt are attached to one expense:

- the invoice should normally be the `primary_document`
- the receipt should normally be a `supporting_document`
- prefill should default to the primary document
