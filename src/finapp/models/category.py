"""Categorization, payees, tags, and rules."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finapp.db.base import Base
from finapp.models.enums import RuleMatchType
from finapp.models.mixins import TimestampMixin


class Category(Base, TimestampMixin):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    is_income: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    color: Mapped[str | None] = mapped_column(String(16))
    icon: Mapped[str | None] = mapped_column(String(64))

    children: Mapped[list[Category]] = relationship(
        back_populates="parent", remote_side="Category.parent_id"
    )
    parent: Mapped[Category | None] = relationship(
        back_populates="children", remote_side="Category.id"
    )


class Payee(Base, TimestampMixin):
    __tablename__ = "payee"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    aliases: Mapped[str | None] = mapped_column(Text)  # JSON list of strings
    default_category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    tax_id: Mapped[str | None] = mapped_column(String(32))


class Tag(Base, TimestampMixin):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    color: Mapped[str | None] = mapped_column(String(16))


transaction_tag = Table(
    "transaction_tag",
    Base.metadata,
    Column("transaction_id", Integer, ForeignKey("transaction.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tag.id"), primary_key=True),
)


class Rule(Base, TimestampMixin):
    __tablename__ = "rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    priority: Mapped[int] = mapped_column(default=100, nullable=False)
    match_type: Mapped[RuleMatchType] = mapped_column(String(16), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    account_scope_id: Mapped[int | None] = mapped_column(ForeignKey("account.id"))
    set_category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    set_payee_id: Mapped[int | None] = mapped_column(ForeignKey("payee.id"))
    set_tags: Mapped[str | None] = mapped_column(Text)  # JSON list
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
