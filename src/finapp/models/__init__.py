"""SQLAlchemy ORM models. Importing this package registers all tables on Base.metadata."""
from __future__ import annotations

from finapp.models.account import Account, AccountHolder, Institution
from finapp.models.ai import AIInteraction, AuditLog
from finapp.models.budget import Budget, Goal
from finapp.models.category import Category, Payee, Rule, Tag, transaction_tag
from finapp.models.currency import Currency, FxRate
from finapp.models.investment import (
    CorporateAction,
    InvestmentTransaction,
    Lot,
    PriceHistory,
    Security,
)
from finapp.models.reconciliation import (
    ParserTemplate,
    ReconciliationMatch,
    ReconciliationSession,
    StatementImport,
)
from finapp.models.transaction import Transaction, TransactionSplit, Transfer

__all__ = [
    "Account",
    "AccountHolder",
    "AIInteraction",
    "AuditLog",
    "Budget",
    "Category",
    "CorporateAction",
    "Currency",
    "FxRate",
    "Goal",
    "Institution",
    "InvestmentTransaction",
    "Lot",
    "ParserTemplate",
    "Payee",
    "PriceHistory",
    "ReconciliationMatch",
    "ReconciliationSession",
    "Rule",
    "Security",
    "StatementImport",
    "Tag",
    "Transaction",
    "TransactionSplit",
    "Transfer",
    "transaction_tag",
]
