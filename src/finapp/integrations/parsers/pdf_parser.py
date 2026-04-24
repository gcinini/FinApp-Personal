"""PDF statement parser.

Two-tier strategy:

1. **Template-driven** — when a `parser_template` (JSON) exists for the institution,
   use it. Templates describe how to locate and parse rows on each page (regex over
   the extracted text, or table extraction with `pdfplumber`).
2. **AI-fallback** — when no template matches, hand the extracted page text to the
   configured LLM provider asking it to return rows in a strict JSON schema; the
   resulting mapping can be persisted as a new `ParserTemplate(learned_by_ai=True)`.

Template schema (JSON)::

    {
        "mode": "regex" | "table",
        "currency": "BRL",
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "thousands_separator": ".",
        "row_regex": "^(?P<date>\\d{2}/\\d{2}/\\d{4})\\s+(?P<desc>.+?)\\s+(?P<amount>-?[\\d.,]+)$",
        "table_settings": {                 // pdfplumber kwargs, used when mode=table
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines"
        },
        "columns": {                        // for mode=table
            "date": 0, "description": 1, "amount": 2
        }
    }
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from finapp.integrations.parsers.base import (
    ParsedStatement,
    ParsedTransaction,
    StatementParser,
    register,
)


def _to_decimal(text: str, decimal_sep: str, thousands_sep: str) -> Decimal:
    s = text.strip().replace(thousands_sep, "")
    if decimal_sep != ".":
        s = s.replace(decimal_sep, ".")
    s = s.replace("\xa0", "").replace(" ", "")
    if s in {"", "-"}:
        return Decimal(0)
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"Cannot parse number: {text!r}") from exc


@register
class PdfStatementParser(StatementParser):
    format = "PDF"

    def can_parse(self, path: Path) -> bool:
        if path.suffix.lower() != ".pdf":
            return False
        try:
            with path.open("rb") as fh:
                return fh.read(5) == b"%PDF-"
        except OSError:
            return False

    def parse(
        self, path: Path, *, template: dict[str, Any] | None = None
    ) -> ParsedStatement:
        try:
            import pdfplumber  # imported lazily so the dep is optional at runtime
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "pdfplumber is required for PDF statement parsing. "
                "Install it: pip install pdfplumber"
            ) from exc

        if template is None:
            return self._parse_with_ai_fallback(path)

        mode = template.get("mode", "regex")
        currency = (template.get("currency") or "BRL").upper()
        date_fmt = template.get("date_format", "%d/%m/%Y")
        dec_sep = template.get("decimal_separator", ",")
        th_sep = template.get("thousands_separator", ".")

        txs: list[ParsedTransaction] = []

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                if mode == "table":
                    table_settings = template.get("table_settings") or {}
                    columns = template.get("columns") or {}
                    col_date = int(columns.get("date", 0))
                    col_desc = int(columns.get("description", 1))
                    col_amount = int(columns.get("amount", 2))
                    for table in page.extract_tables(table_settings) or []:
                        for row in table:
                            if not row or not row[col_date]:
                                continue
                            try:
                                posted = datetime.strptime(
                                    str(row[col_date]).strip(), date_fmt
                                ).date()
                                amount = _to_decimal(str(row[col_amount]), dec_sep, th_sep)
                            except (ValueError, IndexError):
                                continue
                            description = str(row[col_desc] or "").strip()
                            txs.append(
                                _make_tx(posted, amount, currency, description, row)
                            )
                else:
                    pattern = re.compile(template["row_regex"], re.MULTILINE)
                    text = page.extract_text() or ""
                    for m in pattern.finditer(text):
                        try:
                            posted = datetime.strptime(m.group("date"), date_fmt).date()
                            amount = _to_decimal(m.group("amount"), dec_sep, th_sep)
                        except ValueError:
                            continue
                        description = m.group("desc").strip()
                        txs.append(
                            _make_tx(posted, amount, currency, description, m.groupdict())
                        )

        period_start = min((t.posted_date for t in txs), default=None)
        period_end = max((t.posted_date for t in txs), default=None)

        return ParsedStatement(
            account_hint=None,
            currency_hint=currency,
            period_start=period_start,
            period_end=period_end,
            opening_balance=None,
            closing_balance=None,
            transactions=txs,
        )

    # ----- AI fallback ---------------------------------------------------

    def _parse_with_ai_fallback(self, path: Path) -> ParsedStatement:
        """Stub for AI-assisted PDF layout detection.

        Concrete implementation will:
          1. Extract page text via pdfplumber.
          2. Send a chunked prompt to `LLMProvider.complete_json(...)`
             requesting rows in a strict JSON schema.
          3. Persist the inferred layout as a `ParserTemplate(learned_by_ai=True)`
             so future imports skip the LLM round-trip.
        """
        return ParsedStatement(
            account_hint=None,
            currency_hint=None,
            period_start=None,
            period_end=None,
            opening_balance=None,
            closing_balance=None,
            transactions=[],
        )


def _make_tx(
    posted: date,
    amount: Decimal,
    currency: str,
    description: str,
    raw: Any,
) -> ParsedTransaction:
    h = hashlib.sha1(
        f"{posted}|{amount}|{currency}|{description}".encode(),
        usedforsecurity=False,
    ).hexdigest()
    return ParsedTransaction(
        posted_date=posted,
        amount=amount,
        currency=currency,
        description=description,
        external_id=h,
        raw={"raw": raw} if not isinstance(raw, dict) else dict(raw),
    )
