# UK Rules and Assumptions

This document is not legal advice. It records the domain assumptions the product uses.

## Company context

The application is built for:

- a UK private limited company
- one director
- early-stage operations
- no VAT registration in v1

## Director-paid business expenses

If the director pays for a legitimate company expense personally, the app should treat that as money the director lent to the company.

Operational behaviour:

- create an `Expense`
- create a linked `DirectorLoanEntry`
- set direction to `loan_to_company`

## Repayments

If the company later repays the director, the app should record a DLA ledger movement with:

- entry type `repayment_to_director`
- direction `repayment_to_director`

The repayment does not delete or rewrite the original expense record.

## Pre-trading expenses

The app should support a boolean or explicit flag for `is_pre_trading`.

This is an operational classification used so the user and later accountant can distinguish expenses incurred before the company started trading.

The application should not pretend to make a final tax judgment. It should preserve the factual record and the user's classification.

## VAT

VAT is disabled in v1.

Implications:

- no VAT fields are required in the primary workflow
- no VAT calculations are shown
- all amounts are stored as gross cash amounts for operational simplicity

## Currency

Base currency in v1 is `GBP`.

Foreign-currency support may be added later, but the initial workflow should be optimised for UK cash accounting records in pounds sterling.

## Categories

Categories are operational categories, not a complete statutory chart of accounts.

Initial categories should be concise and practical:

- software subscriptions
- hosting and infrastructure
- domains and DNS
- equipment and hardware
- office supplies
- professional fees
- bank and payment fees
- marketing and branding
- travel
- training and books
- communications
- other
