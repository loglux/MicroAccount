from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expense_date: Mapped[date] = mapped_column(Date, index=True)
    supplier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    category_code: Mapped[str] = mapped_column(String(100), index=True)
    paid_by: Mapped[str] = mapped_column(String(50), default="director_personal_card")
    expense_type: Mapped[str] = mapped_column(String(50), default="director_loan_funded_expense")
    is_pre_trading: Mapped[bool] = mapped_column(Boolean, default=False)
    incurred_before_incorporation: Mapped[bool] = mapped_column(Boolean, default=False)
    cost_treatment: Mapped[str] = mapped_column(String(50), default="revenue")
    use_type: Mapped[str] = mapped_column(String(50), default="business_only")
    business_use_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    is_business_use: Mapped[bool] = mapped_column(Boolean, default=True)
    allowable_for_ct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="recorded")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    loan_entries: Mapped[list[DirectorLoanEntry]] = relationship(back_populates="expense")
    attachments: Mapped[list[Attachment]] = relationship(back_populates="expense")
    incoming_documents: Mapped[list[IncomingDocument]] = relationship(
        back_populates="linked_expense"
    )


class DirectorLoanEntry(Base):
    __tablename__ = "director_loan_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    entry_type: Mapped[str] = mapped_column(String(50), index=True)
    direction: Mapped[str] = mapped_column(String(50), index=True)
    amount_gbp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    reference: Mapped[str] = mapped_column(String(255))
    expense_id: Mapped[int | None] = mapped_column(ForeignKey("expenses.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    expense: Mapped[Expense | None] = relationship(back_populates="loan_entries")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_path: Mapped[str] = mapped_column(String(500))
    document_role: Mapped[str] = mapped_column(String(50), default="supporting_document")
    processing_status: Mapped[str] = mapped_column(String(50), default="queued")
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    expense: Mapped[Expense] = relationship(back_populates="attachments")
    extractions: Mapped[list[DocumentExtraction]] = relationship(back_populates="attachment")


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attachment_id: Mapped[int] = mapped_column(ForeignKey("attachments.id"), index=True)
    extractor_name: Mapped[str] = mapped_column(String(100))
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_guess: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_number_guess: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_date_guess: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_amount_guess: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency_guess: Mapped[str | None] = mapped_column(String(10), nullable=True)
    confidence_score: Mapped[str | None] = mapped_column(String(20), nullable=True)
    parser_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    attachment: Mapped[Attachment] = relationship(back_populates="extractions")


class IncomingDocument(Base):
    __tablename__ = "incoming_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    linked_expense_id: Mapped[int | None] = mapped_column(ForeignKey("expenses.id"), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_path: Mapped[str] = mapped_column(String(500))
    processing_status: Mapped[str] = mapped_column(String(50), default="queued")
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    supplier_guess: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_number_guess: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_date_guess: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_amount_guess: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency_guess: Mapped[str | None] = mapped_column(String(10), nullable=True)
    confidence_score: Mapped[str | None] = mapped_column(String(20), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parser_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    linked_expense: Mapped[Expense | None] = relationship(back_populates="incoming_documents")


class AccountMapping(Base):
    __tablename__ = "account_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    account_code: Mapped[str] = mapped_column(String(20), index=True)
    account_name: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
