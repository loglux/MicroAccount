from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    expense_date: date
    supplier_name: str | None = Field(default=None, max_length=255)
    description: str = Field(min_length=2, max_length=500)
    amount_gbp: Decimal = Field(gt=0)
    category_code: str = Field(min_length=2, max_length=100)
    is_pre_trading: bool = False
    incurred_before_incorporation: bool = False
    cost_treatment: str = Field(default="revenue", max_length=50)
    use_type: str = Field(default="business_only", max_length=50)
    business_use_percent: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    allowable_for_ct: bool | None = None


class RepaymentCreate(BaseModel):
    entry_date: date
    amount_gbp: Decimal = Field(gt=0)
    reference: str = Field(min_length=2, max_length=255)
    notes: str | None = None


class IncomingDocumentCreateExpense(BaseModel):
    category_code: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    supplier_name: str | None = Field(default=None, max_length=255)
    expense_date: date | None = None
    amount_gbp: Decimal | None = Field(default=None, gt=0)
    is_pre_trading: bool = False
    incurred_before_incorporation: bool = False
    cost_treatment: str = Field(default="revenue", max_length=50)
    use_type: str = Field(default="business_only", max_length=50)
    business_use_percent: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class IncomingDocumentReviewUpdate(BaseModel):
    document_type: str | None = Field(default=None, max_length=50)
    supplier_guess: str | None = Field(default=None, max_length=255)
    reference_number_guess: str | None = Field(default=None, max_length=100)
    document_date_guess: str | None = Field(default=None, max_length=50)
    total_amount_guess: str | None = Field(default=None, max_length=50)
    currency_guess: str | None = Field(default=None, max_length=10)
    parser_notes: str | None = None
