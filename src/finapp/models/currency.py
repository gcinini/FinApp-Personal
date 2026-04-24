"""Currency catalog + FX rate snapshots."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finapp.db.base import Base
from finapp.models.enums import FxSource
from finapp.models.mixins import TimestampMixin


class Currency(Base, TimestampMixin):
    __tablename__ = "currency"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)  # ISO 4217
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    decimal_places: Mapped[int] = mapped_column(default=2, nullable=False)


class FxRate(Base, TimestampMixin):
    __tablename__ = "fx_rate"
    __table_args__ = (
        UniqueConstraint("rate_date", "base_currency", "quote_currency", "source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    base_currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    quote_currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(20, 10), nullable=False)
    source: Mapped[FxSource] = mapped_column(String(16), nullable=False)
