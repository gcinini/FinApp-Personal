"""Statement parser registry — importing this module registers all built-in parsers."""
from __future__ import annotations

from finapp.integrations.parsers.base import (
    ParsedStatement,
    ParsedTransaction,
    StatementParser,
    all_parsers,
    detect_parser,
    register,
)

# Import side-effects register parsers in the global registry.
from finapp.integrations.parsers import csv_parser  # noqa: F401
from finapp.integrations.parsers import ofx_parser  # noqa: F401
from finapp.integrations.parsers import pdf_parser  # noqa: F401

__all__ = [
    "ParsedStatement",
    "ParsedTransaction",
    "StatementParser",
    "all_parsers",
    "detect_parser",
    "register",
]
