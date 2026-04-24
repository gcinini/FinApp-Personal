"""Institutions + accounts + holders."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finapp.db.base import Base
from finapp.models.enums import AccountType, InstitutionType
from finapp.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from finapp.models.transaction import Transaction


class Institution(Base, TimestampMixin):
    __tablename__ = "institution"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    type: Mapped[InstitutionType] = mapped_column(String(16), nullable=False)
    swift_bic: Mapped[str | None] = mapped_column(String(11))
    routing_or_ispb: Mapped[str | None] = mapped_column(String(32))
    website: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    accounts: Mapped[list[Account]] = relationship(back_populates="institution")


class Account(Base, TimestampMixin):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institution.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(String(16), nullable=False)
    currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    account_number_masked: Mapped[str | None] = mapped_column(String(64))
    opening_balance_minor: Mapped[int] = mapped_column(default=0, nullable=False)
    opening_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tax_country: Mapped[str | None] = mapped_column(String(2))
    notes: Mapped[str | None] = mapped_column(Text)

    institution: Mapped[Institution] = relationship(back_populates="accounts")
    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class AccountHolder(Base, TimestampMixin):
    __tablename__ = "account_holder"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(32))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
