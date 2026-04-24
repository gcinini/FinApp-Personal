"""Enumerations used across the data model."""
from __future__ import annotations

import enum


class InstitutionType(str, enum.Enum):
    BANK = "BANK"
    BROKERAGE = "BROKERAGE"
    CARD_ISSUER = "CARD_ISSUER"
    EXCHANGE = "EXCHANGE"
    OTHER = "OTHER"


class AccountType(str, enum.Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CREDIT_CARD = "CREDIT_CARD"
    BROKERAGE = "BROKERAGE"
    INVESTMENT = "INVESTMENT"
    LOAN = "LOAN"
    CASH = "CASH"
    CRYPTO_WALLET = "CRYPTO_WALLET"
    OTHER = "OTHER"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLEARED = "CLEARED"
    RECONCILED = "RECONCILED"
    VOID = "VOID"


class TransactionSource(str, enum.Enum):
    MANUAL = "MANUAL"
    IMPORT_OFX = "IMPORT_OFX"
    IMPORT_CSV = "IMPORT_CSV"
    IMPORT_PDF = "IMPORT_PDF"
    IMPORT_XLSX = "IMPORT_XLSX"
    IMPORT_QIF = "IMPORT_QIF"
    AI_SUGGESTED = "AI_SUGGESTED"


class SecurityType(str, enum.Enum):
    STOCK = "STOCK"
    ETF = "ETF"
    FII = "FII"
    FUND = "FUND"
    BOND = "BOND"
    TESOURO_DIRETO = "TESOURO_DIRETO"
    CDB = "CDB"
    LCI = "LCI"
    LCA = "LCA"
    CRYPTO = "CRYPTO"
    OPTION = "OPTION"
    OTHER = "OTHER"


class InvestmentTxType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    INTEREST = "INTEREST"
    JCP = "JCP"  # Juros sobre Capital Próprio (BR)
    SPLIT = "SPLIT"
    MERGER = "MERGER"
    BONUS = "BONUS"
    FEE = "FEE"
    TAX_WITHHELD = "TAX_WITHHELD"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    REINVEST = "REINVEST"


class CostBasisMethod(str, enum.Enum):
    FIFO = "FIFO"
    LIFO = "LIFO"
    AVERAGE = "AVERAGE"


class ReconciliationStatus(str, enum.Enum):
    OPEN = "OPEN"
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"


class MatchType(str, enum.Enum):
    EXACT = "EXACT"
    FUZZY = "FUZZY"
    AI = "AI"
    MANUAL = "MANUAL"


class RuleMatchType(str, enum.Enum):
    REGEX = "REGEX"
    CONTAINS = "CONTAINS"
    AMOUNT_RANGE = "AMOUNT_RANGE"
    AI_EMBEDDING = "AI_EMBEDDING"


class FxSource(str, enum.Enum):
    BCB_PTAX = "BCB_PTAX"
    ECB = "ECB"
    YAHOO = "YAHOO"
    MANUAL = "MANUAL"
