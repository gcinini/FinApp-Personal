"""Statement parser interfaces and registry.

Concrete parsers live in `finapp.integrations.parsers.*` and produce a stream of
`ParsedTransaction` records that the import service can then dedupe, categorize,
and persist.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ParsedTransaction:
    """Source-format-agnostic transaction extracted from a statement."""

    posted_date: date
    amount: Decimal           # signed; negative = debit
    currency: str
    description: str
    external_id: str | None = None   # FITID for OFX, hash for CSV/PDF rows
    value_date: date | None = None
    balance_after: Decimal | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedStatement:
    account_hint: str | None
    currency_hint: str | None
    period_start: date | None
    period_end: date | None
    opening_balance: Decimal | None
    closing_balance: Decimal | None
    transactions: list[ParsedTransaction] = field(default_factory=list)


class StatementParser(ABC):
    """Base class for all statement parsers."""

    #: Short identifier (e.g. "OFX", "CSV", "PDF").
    format: str = ""

    @abstractmethod
    def can_parse(self, path: Path) -> bool:
        """Cheap probe — inspect filename / first bytes."""

    @abstractmethod
    def parse(self, path: Path, *, template: dict[str, Any] | None = None) -> ParsedStatement:
        """Read the file and return a ParsedStatement."""


_REGISTRY: list[StatementParser] = []


def register(parser_cls_or_instance):  # type: ignore[no-untyped-def]
    """Decorator: accepts either a parser class or a parser instance."""
    if isinstance(parser_cls_or_instance, type):
        _REGISTRY.append(parser_cls_or_instance())
    else:
        _REGISTRY.append(parser_cls_or_instance)
    return parser_cls_or_instance


def all_parsers() -> Iterable[StatementParser]:
    return tuple(_REGISTRY)


def detect_parser(path: Path) -> StatementParser | None:
    for p in _REGISTRY:
        if p.can_parse(path):
            return p
    return None
