"""Transactions, splits, transfers."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finapp.db.base import Base
from finapp.models.category import transaction_tag
from finapp.models.enums import TransactionSource, TransactionStatus
from finapp.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from finapp.models.account import Account
    from finapp.models.category import Tag


class Transaction(Base, TimestampMixin):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False, index=True)
    posted_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value_date: Mapped[date | None] = mapped_column(Date)
    amount_minor: Mapped[int] = mapped_column(nullable=False)  # signed
    currency: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)

    description_raw: Mapped[str | None] = mapped_column(Text)
    description_clean: Mapped[str | None] = mapped_column(Text)
    memo: Mapped[str | None] = mapped_column(Text)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    payee_id: Mapped[int | None] = mapped_column(ForeignKey("payee.id"))

    external_id: Mapped[str | None] = mapped_column(String(128), index=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("statement_import.id"))

    status: Mapped[TransactionStatus] = mapped_column(
        String(16), default=TransactionStatus.PENDING, nullable=False
    )
    source: Mapped[TransactionSource] = mapped_column(
        String(16), default=TransactionSource.MANUAL, nullable=False
    )

    transfer_pair_id: Mapped[int | None] = mapped_column(ForeignKey("transaction.id"))
    reconciliation_match_id: Mapped[int | None] = mapped_column(
        ForeignKey("reconciliation_match.id")
    )
    attachment_path: Mapped[str | None] = mapped_column(String(512))

    account: Mapped[Account] = relationship(back_populates="transactions")
    splits: Mapped[list[TransactionSplit]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )
    tags: Mapped[list[Tag]] = relationship(secondary=transaction_tag)


class TransactionSplit(Base):
    __tablename__ = "transaction_split"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transaction.id"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    amount_minor: Mapped[int] = mapped_column(nullable=False)
    memo: Mapped[str | None] = mapped_column(Text)

    transaction: Mapped[Transaction] = relationship(back_populates="splits")


class Transfer(Base, TimestampMixin):
    """Explicit cross-account (potentially cross-currency) transfer link."""

    __tablename__ = "transfer"

    id: Mapped[int] = mapped_column(primary_key=True)
    debit_transaction_id: Mapped[int] = mapped_column(ForeignKey("transaction.id"), nullable=False)
    credit_transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transaction.id"), nullable=False
    )
    fx_rate: Mapped[float | None] = mapped_column(Numeric(20, 10))
    fees_minor: Mapped[int] = mapped_column(default=0, nullable=False)
    fees_currency: Mapped[str | None] = mapped_column(ForeignKey("currency.code"))
    notes: Mapped[str | None] = mapped_column(Text)
