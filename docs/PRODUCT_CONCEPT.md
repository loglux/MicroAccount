# Product Concept

## What this product is

`MicroAccount` is not a generic accounting app and not a lightweight clone of `Xero`.

It is a `financial operating system for an early-stage UK limited company` with one director, limited budget, and a practical need to keep records clean until a fuller accounting stack or an external accountant takes over.

## Core company reality

Assume this operating model unless the documentation changes:

- UK private limited company
- one director
- low-cost, self-hosted or local-first operation
- many company expenses paid personally by the director
- repayments happen later from the company back to the director
- income may appear later, but is not yet the dominant workflow
- VAT is not enabled in the current scope

## Main user problem

The company cannot justify a commercial accounting subscription yet, but it still needs:

- a reliable expense register
- supporting invoice and receipt storage
- a clean Director's Loan Account record
- a simple way to record repayments
- a path to track income later
- clean exports for accountant handoff

## Product definition

The product should be understood as four related registers:

1. `Expenses`
   The main register of company costs.
2. `Documents`
   The evidence and intake workflow for invoices, receipts, and review.
3. `Money`
   Director loan movements, repayments, and later bank transactions.
4. `Income`
   Incoming money records once revenue starts.

This is the correct mental model for the product. It is broader than a DLA helper, but narrower than full bookkeeping software.

## Primary object

For the current product phase, the primary object is:

- `Expense`

Supporting objects:

- `Document`
- `DirectorLoanEntry`
- `Repayment`
- `IncomeRecord` later

Meaning:

- a document helps create or support an expense
- an expense creates a DLA effect when paid personally
- a repayment changes the DLA balance
- income is a separate register, not a subtype of expense

## Primary workflows

### 1. Capture a company expense

The user either:

- uploads a document and reviews it first
- or enters the expense manually

Result:

- an `Expense` is created
- supporting evidence is linked
- if paid personally, a DLA entry is created

### 2. Review and classify

The user confirms:

- supplier
- amount
- date
- category
- UK review flags

This is where business clarity matters most.

### 3. Record repayment

The user records money paid back by the company to the director.

Result:

- DLA balance is reduced
- no new expense is created

### 4. Record income later

When revenue begins, the user should be able to record simple income entries without converting the whole product into a full invoicing suite.

## Product boundaries

The product must optimise for:

- practical recordkeeping
- clean accountant handoff
- low operating complexity
- clear UK terminology
- modular growth

The product must avoid becoming:

- a generic ERP
- a full chart-of-accounts driven bookkeeping suite
- a bloated document management app
- a bank-integration project before the core registers work well

## Product principle

The application should always answer these questions clearly:

- what did the company spend
- who paid for it
- what evidence exists
- how much the company owes the director
- what has already been repaid
- what income has been received

If a screen or feature does not help answer one of those questions, it is probably secondary and should not dominate the UX.
