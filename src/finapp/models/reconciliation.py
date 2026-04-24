"""Statement imports + reconciliation sessions/matches."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finapp.db.base import Base
from finapp.models.enums import MatchType, ReconciliationStatus
from finapp.models.mixins import TimestampMixin


class StatementImport(Base, TimestampMixin):
    __tablename__ = "statement_import"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    file_format: Mapped[str] = mapped_column(String(16), nullable=False)  # OFX|CSV|PDF|XLSX|QIF
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    opening_balance_minor: Mapped[int | None] = mapped_column()
    closing_balance_minor: Mapped[int | None] = mapped_column()
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="OK", nullable=False)
    parser_template_id: Mapped[int | None] = mapped_column(ForeignKey("parser_template.id"))


class ParserTemplate(Base, TimestampMixin):
    """Reusable column / layout mapping for CSV or PDF imports per institution."""

    __tablename__ = "parser_template"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institution.id"))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    file_format: Mapped[str] = mapped_column(String(16), nullable=False)  # CSV|PDF
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    learned_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ReconciliationSession(Base, TimestampMixin):
    __tablename__ = "reconciliation_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False)
    statement_import_id: Mapped[int | None] = mapped_column(ForeignKey("statement_import.id"))
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    expected_balance_minor: Mapped[int] = mapped_column(nullable=False)
    actual_balance_minor: Mapped[int] = mapped_column(nullable=False)
    difference_minor: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[ReconciliationStatus] = mapped_column(
        String(16), default=ReconciliationStatus.OPEN, nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReconciliationMatch(Base, TimestampMixin):
    __tablename__ = "reconciliation_match"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("reconciliation_session.id"), nullable=False, index=True
    )
    book_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transaction.id"))
    statement_external_id: Mapped[str | None] = mapped_column(String(128))
    statement_amount_minor: Mapped[int | None] = mapped_column()
    statement_date: Mapped[date | None] = mapped_column(Date)
    statement_description: Mapped[str | None] = mapped_column(Text)
    match_type: Mapped[MatchType] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(6, 4), default=1.0, nullable=False)
    reviewed_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
