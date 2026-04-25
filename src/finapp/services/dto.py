"""Data Transfer Objects for service → GUI communication.

These frozen dataclasses ensure the GUI never touches live ORM objects,
avoiding lazy-loading issues with closed sessions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class InstitutionSummary:
    id: int
    name: str
    country: str
    type: str
    account_count: int


@dataclass(frozen=True, slots=True)
class AccountSummary:
    id: int
    name: str
    institution_id: int
    institution_name: str
    account_type: str
    currency: str
    currency_symbol: str
    balance_minor: int
    is_active: bool


@dataclass(frozen=True, slots=True)
class TransactionRow:
    id: int
    account_id: int
    account_name: str
    posted_date: date
    description: str
    category_name: str | None
    amount_minor: int
    currency: str
    currency_symbol: str
    status: str
    source: str


@dataclass(frozen=True, slots=True)
class CategoryItem:
    id: int
    name: str
    parent_id: int | None
    is_income: bool


@dataclass(frozen=True, slots=True)
class CurrencyBalance:
    currency: str
    symbol: str
    total_minor: int
    decimal_places: int
