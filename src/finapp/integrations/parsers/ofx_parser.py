"""OFX / QFX statement parser (stub)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from finapp.integrations.parsers.base import (
    ParsedStatement,
    ParsedTransaction,
    StatementParser,
    register,
)


@register
class OfxStatementParser(StatementParser):
    format = "OFX"

    def can_parse(self, path: Path) -> bool:
        if path.suffix.lower() not in {".ofx", ".qfx"}:
            return False
        try:
            with path.open("rb") as fh:
                head = fh.read(512).lower()
            return b"ofx" in head
        except OSError:
            return False

    def parse(
        self, path: Path, *, template: dict[str, Any] | None = None
    ) -> ParsedStatement:
        try:
            from ofxparse import OfxParser  # lazy import
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "ofxparse is required for OFX/QFX import. Install with: pip install ofxparse"
            ) from exc

        with path.open("rb") as fh:
            ofx = OfxParser.parse(fh)

        txs: list[ParsedTransaction] = []
        period_start: date | None = None
        period_end: date | None = None
        currency_hint: str | None = None
        opening: Decimal | None = None
        closing: Decimal | None = None
        account_hint: str | None = None

        for acc in ofx.accounts:
            account_hint = getattr(acc, "account_id", None) or account_hint
            stmt = acc.statement
            currency_hint = getattr(stmt, "currency", None) or currency_hint
            if getattr(stmt, "balance", None) is not None:
                closing = Decimal(str(stmt.balance))
            for t in stmt.transactions:
                posted = t.date.date() if hasattr(t.date, "date") else t.date
                amount = Decimal(str(t.amount))
                desc = (t.payee or t.memo or "").strip()
                txs.append(
                    ParsedTransaction(
                        posted_date=posted,
                        amount=amount,
                        currency=currency_hint or "USD",
                        description=desc,
                        external_id=getattr(t, "id", None),
                        raw={"type": getattr(t, "type", None)},
                    )
                )
                period_start = posted if period_start is None else min(period_start, posted)
                period_end = posted if period_end is None else max(period_end, posted)

        return ParsedStatement(
            account_hint=account_hint,
            currency_hint=currency_hint,
            period_start=period_start,
            period_end=period_end,
            opening_balance=opening,
            closing_balance=closing,
            transactions=txs,
        )
