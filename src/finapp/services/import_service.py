"""Statement import service.

Coordinates parser selection, dedup against existing transactions, persistence,
and (later) rule application.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from finapp.integrations.parsers import detect_parser
from finapp.integrations.parsers.base import ParsedStatement, StatementParser
from finapp.logging_setup import get_logger
from finapp.models import Account, StatementImport, Transaction
from finapp.models.enums import TransactionSource, TransactionStatus
from finapp.money import to_minor

log = get_logger(__name__)

_FORMAT_TO_SOURCE = {
    "OFX": TransactionSource.IMPORT_OFX,
    "CSV": TransactionSource.IMPORT_CSV,
    "PDF": TransactionSource.IMPORT_PDF,
    "XLSX": TransactionSource.IMPORT_XLSX,
    "QIF": TransactionSource.IMPORT_QIF,
}


class ImportService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def import_file(
        self,
        path: Path,
        account_id: int,
        *,
        template: dict[str, Any] | None = None,
        parser: StatementParser | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        path = Path(path)
        account = self.session.get(Account, account_id)
        if account is None:
            raise ValueError(f"Account {account_id} not found")

        parser = parser or detect_parser(path)
        if parser is None:
            raise ValueError(f"No parser found for {path.name}")

        log.info("import.parse", file=str(path), parser=parser.format)
        parsed: ParsedStatement = parser.parse(path, template=template)

        file_hash = _sha256(path)

        existing = self.session.execute(
            select(StatementImport).where(StatementImport.file_hash == file_hash)
        ).scalar_one_or_none()
        if existing and not dry_run:
            log.warning("import.duplicate_file", file_hash=file_hash, import_id=existing.id)
            return {"created": 0, "duplicates": len(parsed.transactions), "import_id": existing.id}

        batch = StatementImport(
            account_id=account_id,
            file_path=str(path.resolve()),
            file_hash=file_hash,
            file_format=parser.format,
            period_start=parsed.period_start,
            period_end=parsed.period_end,
            opening_balance_minor=(
                to_minor(parsed.opening_balance, account.currency)
                if parsed.opening_balance is not None
                else None
            ),
            closing_balance_minor=(
                to_minor(parsed.closing_balance, account.currency)
                if parsed.closing_balance is not None
                else None
            ),
            imported_at=datetime.now(tz=timezone.utc),
        )
        self.session.add(batch)
        self.session.flush()

        source = _FORMAT_TO_SOURCE.get(parser.format, TransactionSource.IMPORT_CSV)

        created = 0
        duplicates = 0
        for ptx in parsed.transactions:
            currency = ptx.currency or account.currency
            ext_id = ptx.external_id

            if ext_id:
                dup = self.session.execute(
                    select(Transaction).where(
                        Transaction.account_id == account_id,
                        Transaction.external_id == ext_id,
                    )
                ).scalar_one_or_none()
                if dup is not None:
                    duplicates += 1
                    continue

            tx = Transaction(
                account_id=account_id,
                posted_date=ptx.posted_date,
                value_date=ptx.value_date,
                amount_minor=to_minor(ptx.amount, currency),
                currency=currency,
                description_raw=ptx.description,
                description_clean=ptx.description,
                external_id=ext_id,
                import_batch_id=batch.id,
                status=TransactionStatus.CLEARED,
                source=source,
            )
            self.session.add(tx)
            created += 1

        if dry_run:
            self.session.rollback()
        else:
            self.session.flush()

        log.info("import.done", created=created, duplicates=duplicates, file=str(path))
        return {"created": created, "duplicates": duplicates, "import_id": batch.id}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
