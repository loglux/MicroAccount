# IA And UX Blueprint

## Product UI thesis

The interface must feel like a focused internal operating tool, not a dashboard experiment and not a fake SaaS shell.

The app should be organised around `working surfaces`, not around decorative overview panels.

## Screen model

### `/expenses`

This is the main screen of the product.

Purpose:

- view the company expense register
- add a new expense manually
- inspect evidence already linked to an expense
- move into document-first intake when needed

Primary object:

- `Expense`

Primary action:

- `Add expense`

Secondary action:

- `Create from document`

Expected layout:

- large expense table as the primary workspace
- narrow side rail for manual expense entry and short guidance
- filters above the table
- clicking the description opens `/expenses/{id}` for editing

### `/expenses/{id}`

Detail and edit view for a single expense. Clicked from the register by the expense description.

Purpose:

- edit any field on the expense (including the UK review flags)
- see and manage attached evidence files
- delete the expense when it was recorded by mistake

Primary object:

- `Expense`

Primary action:

- `Save changes`

Secondary actions:

- attach new evidence files (late upload)
- remove an individual attachment
- delete the whole expense

Editing `amount_gbp` or `expense_date` must also update the linked `loan_to_company` DLA entry so the ledger stays consistent. Deleting the expense cascades to its attachments, attachment files on disk, and the linked DLA entry.

### `/documents`

This is the document intake and review workspace.

Purpose:

- upload one file
- review extracted fields
- correct parsed metadata
- create an expense
- move a file to holding
- delete a temporary file

Primary object:

- `Incoming document under review`

Primary action:

- `Create expense from document`

Expected layout:

- one review surface
- one upload action
- one holding list
- no competing summary sections

### `/dla`

This is the money movement screen for the director loan account.

Purpose:

- inspect running balance
- record repayments
- review the ledger

Primary object:

- `DirectorLoanEntry`

Primary action:

- `Record repayment`

Expected layout:

- ledger as the main surface
- side rail for repayment entry
- compact balance summary

### `/income`

Simple separate register for money received by the company. Kept deliberately minimal: no categories, no attachments, no document-review workflow. It is not a subtype of expense.

Purpose:

- record incoming money
- keep a simple revenue register
- provide a running total without tying into the DLA balance

Primary object:

- `IncomeRecord`

Primary action:

- `Save income` (side-rail form)

Expected layout:

- ledger as the main surface
- filter bar with search + date range
- side rail with the record-income form
- compact summary showing total received and record count

### `/settings`

This screen is for rules and defaults, not daily operations.

Purpose:

- manage categories
- manage account mappings
- manage supplier rules
- manage company defaults

## Home screen rule

The product should not lead with a decorative dashboard.

Preferred behaviour:

- `/` redirects to `/expenses`

Alternative:

- `/` remains a very compact operational overview, but only if it directly helps users enter the main workflow faster

## Navigation model

Primary navigation should reflect the real operational structure:

- `Expenses`
- `Documents`
- `DLA`
- `Income` later
- `Settings` later

Avoid equal visual weight for every area when only one area is primary in daily use.

## UX principles

### 1. One screen, one job

Do not mix:

- intake
- register
- review
- ledger
- settings

into one overloaded page.

### 2. One primary action per screen

Every screen should make the next action obvious.

### 3. Registers over dashboards

This product is a record system. Tables and reviewed records matter more than summary chrome.

### 4. Document assistance, not document dominance

Documents matter as evidence and intake helpers, but they are not the main accounting object.

### 5. UK-first language

Use:

- `Business expense paid personally`
- `Director loan to company`
- `Repayment to director`
- `Company owes director`

Avoid abstract ERP language.

## Visual direction

The visual system should communicate operational seriousness:

- strong contrast in navigation
- clear typography
- dense but readable tables
- side rails for forms and context
- minimal decorative chrome
- no card mosaic dashboard pattern

## What to remove from the current UX direction

- overview-first design
- equal emphasis on every section
- duplicated create flows on multiple screens
- decorative empty space without meaning
- form sprawl
- card-heavy pseudo-dashboard layouts

## Near-term implementation order

1. make `/expenses` the true home screen
2. simplify `/documents` into a proper review inbox
3. keep `/dla` narrow and clear
4. add `/income` as a minimal separate register
5. add `/settings` only after the main operational flows are stable
