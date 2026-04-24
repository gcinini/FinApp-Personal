"""CSV statement parser.

Supports per-institution mapping templates (stored in the `parser_template` table) so
the same parser can read Nubank, Itaú, Chase, Fidelity, etc. without code changes.

Template schema (JSON)::

    {
        "delimiter": ",",
        "encoding": "utf-8",
        "skip_rows": 0,
        "date_format": "%Y-%m-%d",
        "decimal_separator": ".",
        "thousands_separator": ",",
        "currency": "BRL",
        "columns": {
            "date":        "Data",
            "description": "Histórico",
            "amount":      "Valor",
            "external_id": "Identificador",   // optional
            "debit":       null,              // alternative to "amount"
            "credit":      null,
            "value_date":  null,
            "balance":     null
        }
    }
"""
from __future__ import annotations

import csv
import hashlib
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import chardet

from finapp.integrations.parsers.base import (
    ParsedStatement,
    ParsedTransaction,
    StatementParser,
    register,
)


def _sniff_encoding(path: Path) -> str:
    raw = path.read_bytes()[:8192]
    guess = chardet.detect(raw)
    return guess.get("encoding") or "utf-8"


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


def _parse_date(text: str, fmt: str) -> date:
    return datetime.strptime(text.strip(), fmt).date()


def _row_hash(row: dict[str, str]) -> str:
    h = hashlib.sha1(usedforsecurity=False)
    for k in sorted(row):
        h.update(f"{k}={row[k]}|".encode())
    return h.hexdigest()


@register
class CsvStatementParser(StatementParser):
    format = "CSV"

    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in {".csv", ".tsv", ".txt"}

    def parse(
        self, path: Path, *, template: dict[str, Any] | None = None
    ) -> ParsedStatement:
        tpl: dict[str, Any] = template or {}
        delimiter: str = tpl.get("delimiter", ",")
        encoding: str = tpl.get("encoding") or _sniff_encoding(path)
        skip_rows: int = int(tpl.get("skip_rows", 0))
        date_fmt: str = tpl.get("date_format", "%Y-%m-%d")
        dec_sep: str = tpl.get("decimal_separator", ".")
        th_sep: str = tpl.get("thousands_separator", ",")
        currency: str = (tpl.get("currency") or "BRL").upper()
        cols: dict[str, str | None] = tpl.get("columns") or {}

        col_date = cols.get("date") or "date"
        col_desc = cols.get("description") or "description"
        col_amount = cols.get("amount")
        col_debit = cols.get("debit")
        col_credit = cols.get("credit")
        col_extid = cols.get("external_id")
        col_value = cols.get("value_date")
        col_balance = cols.get("balance")

        txs: list[ParsedTransaction] = []
        period_start: date | None = None
        period_end: date | None = None

        with path.open("r", encoding=encoding, newline="") as fh:
            for _ in range(skip_rows):
                fh.readline()
            reader = csv.DictReader(fh, delimiter=delimiter)
            for row in reader:
                if not any((v or "").strip() for v in row.values()):
                    continue
                try:
                    posted = _parse_date(row[col_date], date_fmt)
                except (KeyError, ValueError):
                    # Skip rows that don't look like data (footers, etc.).
                    continue

                if col_amount and row.get(col_amount, "").strip():
                    amount = _to_decimal(row[col_amount], dec_sep, th_sep)
                else:
                    debit = (
                        _to_decimal(row.get(col_debit, "0") or "0", dec_sep, th_sep)
                        if col_debit
                        else Decimal(0)
                    )
                    credit = (
                        _to_decimal(row.get(col_credit, "0") or "0", dec_sep, th_sep)
                        if col_credit
                        else Decimal(0)
                    )
                    amount = credit - debit

                description = (row.get(col_desc) or "").strip()
                ext_id = (row.get(col_extid) or "").strip() if col_extid else None
                if not ext_id:
                    ext_id = _row_hash(row)

                value_date = (
                    _parse_date(row[col_value], date_fmt)
                    if col_value and row.get(col_value)
                    else None
                )
                balance = (
                    _to_decimal(row[col_balance], dec_sep, th_sep)
                    if col_balance and row.get(col_balance)
                    else None
                )

                txs.append(
                    ParsedTransaction(
                        posted_date=posted,
                        amount=amount,
                        currency=currency,
                        description=description,
                        external_id=ext_id,
                        value_date=value_date,
                        balance_after=balance,
                        raw=dict(row),
                    )
                )

                period_start = posted if period_start is None else min(period_start, posted)
                period_end = posted if period_end is None else max(period_end, posted)

        return ParsedStatement(
            account_hint=None,
            currency_hint=currency,
            period_start=period_start,
            period_end=period_end,
            opening_balance=None,
            closing_balance=txs[-1].balance_after if txs else None,
            transactions=txs,
        )
