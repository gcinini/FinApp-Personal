"""Securities, lots, investment transactions, prices, corporate actions."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finapp.db.base import Base
from finapp.models.enums import CostBasisMethod, InvestmentTxType, SecurityType
from finapp.models.mixins import TimestampMixin


class Security(Base, TimestampMixin):
    __tablename__ = "security"
    __table_args__ = (UniqueConstraint("symbol", "exchange"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    exchange: Mapped[str | None] = mapped_column(String(16))
    isin: Mapped[str | None] = mapped_column(String(12))
    cusip: Mapped[str | None] = mapped_column(String(9))
    cnpj: Mapped[str | None] = mapped_column(String(18))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    security_type: Mapped[SecurityType] = mapped_column(String(24), nullable=False)
    currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    quote_provider: Mapped[str | None] = mapped_column(String(32))
    metadata_json: Mapped[str | None] = mapped_column(Text)


class Lot(Base, TimestampMixin):
    __tablename__ = "lot"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False, index=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), nullable=False, index=True)
    acquired_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(28, 10), nullable=False)
    cost_basis_minor: Mapped[int] = mapped_column(nullable=False)
    cost_currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    fx_rate_at_acquisition: Mapped[float | None] = mapped_column(Numeric(20, 10))
    source_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("investment_transaction.id")
    )
    cost_basis_method: Mapped[CostBasisMethod] = mapped_column(
        String(8), default=CostBasisMethod.FIFO, nullable=False
    )


class InvestmentTransaction(Base, TimestampMixin):
    __tablename__ = "investment_transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False, index=True)
    security_id: Mapped[int | None] = mapped_column(ForeignKey("security.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settle_date: Mapped[date | None] = mapped_column(Date)
    type: Mapped[InvestmentTxType] = mapped_column(String(16), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(28, 10), default=0, nullable=False)
    price_minor: Mapped[int] = mapped_column(default=0, nullable=False)
    fees_minor: Mapped[int] = mapped_column(default=0, nullable=False)
    taxes_minor: Mapped[int] = mapped_column(default=0, nullable=False)
    currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    linked_cash_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transaction.id"))
    notes: Mapped[str | None] = mapped_column(Text)


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("security_id", "price_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), nullable=False, index=True)
    price_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open: Mapped[float | None] = mapped_column(Numeric(20, 6))
    high: Mapped[float | None] = mapped_column(Numeric(20, 6))
    low: Mapped[float | None] = mapped_column(Numeric(20, 6))
    close: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    volume: Mapped[int | None] = mapped_column()
    currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)


class CorporateAction(Base, TimestampMixin):
    __tablename__ = "corporate_action"

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), nullable=False, index=True)
    action_date: Mapped[date] = mapped_column(Date, nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)  # SPLIT, MERGER, ...
    ratio_numerator: Mapped[float | None] = mapped_column(Numeric(20, 6))
    ratio_denominator: Mapped[float | None] = mapped_column(Numeric(20, 6))
    cash_amount_minor: Mapped[int | None] = mapped_column()
    currency: Mapped[str | None] = mapped_column(ForeignKey("currency.code"))
    notes: Mapped[str | None] = mapped_column(Text)
