from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.models import IncomeRecord
from app.domain.policies.uk import GBP


@dataclass(slots=True)
class IncomeInput:
    income_date: date
    source_name: str
    description: str
    amount_gbp: Decimal
    reference: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class IncomeSummary:
    total_received: Decimal
    record_count: int


def create_income(db: Session, payload: IncomeInput) -> IncomeRecord:
    record = IncomeRecord(
        income_date=payload.income_date,
        source_name=payload.source_name.strip(),
        description=payload.description.strip(),
        amount_gbp=payload.amount_gbp,
        currency=GBP,
        reference=(payload.reference or "").strip() or None,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_income_records(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    search_text: str | None = None,
) -> list[IncomeRecord]:
    query = select(IncomeRecord).order_by(
        IncomeRecord.income_date.desc(), IncomeRecord.id.desc()
    )
    if start_date:
        query = query.where(IncomeRecord.income_date >= start_date)
    if end_date:
        query = query.where(IncomeRecord.income_date <= end_date)
    if search_text:
        pattern = f"%{search_text.strip()}%"
        query = query.where(
            or_(
                IncomeRecord.source_name.ilike(pattern),
                IncomeRecord.description.ilike(pattern),
                IncomeRecord.reference.ilike(pattern),
                IncomeRecord.notes.ilike(pattern),
            )
        )
    return list(db.scalars(query).all())


def get_income_summary(db: Session) -> IncomeSummary:
    total_received = Decimal(
        db.scalar(select(func.coalesce(func.sum(IncomeRecord.amount_gbp), 0))) or 0
    )
    record_count = int(db.scalar(select(func.count()).select_from(IncomeRecord)) or 0)
    return IncomeSummary(total_received=total_received, record_count=record_count)
