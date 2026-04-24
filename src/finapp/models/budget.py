"""Budgets and goals."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finapp.db.base import Base
from finapp.models.mixins import TimestampMixin


class Budget(Base, TimestampMixin):
    __tablename__ = "budget"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    period: Mapped[str] = mapped_column(String(16), default="MONTHLY", nullable=False)
    amount_minor: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    rollover: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Goal(Base, TimestampMixin):
    __tablename__ = "goal"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_amount_minor: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date)
    linked_account_id: Mapped[int | None] = mapped_column(ForeignKey("account.id"))
    notes: Mapped[str | None] = mapped_column(Text)
