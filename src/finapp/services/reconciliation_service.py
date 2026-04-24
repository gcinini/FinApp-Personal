"""Reconciliation service — exact / fuzzy / AI matching.

Phase 1 implements exact + fuzzy matching. AI matching is reserved for Phase 4.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finapp.integrations.parsers.base import ParsedTransaction
from finapp.models import ReconciliationMatch, ReconciliationSession, Transaction
from finapp.models.enums import MatchType, ReconciliationStatus, TransactionStatus
from finapp.money import to_minor


@dataclass(slots=True)
class MatchProposal:
    book_transaction_id: int | None
    statement_external_id: str | None
    confidence: float
    match_type: MatchType


class ReconciliationService:
    def __init__(self, session: Session, *, date_tolerance_days: int = 3) -> None:
        self.session = session
        self.date_tolerance = timedelta(days=date_tolerance_days)

    def open_session(
        self,
        account_id: int,
        period_start: date,
        period_end: date,
        expected_balance: Decimal,
        actual_balance: Decimal,
        currency: str,
    ) -> ReconciliationSession:
        sess = ReconciliationSession(
            account_id=account_id,
            period_start=period_start,
            period_end=period_end,
            expected_balance_minor=to_minor(expected_balance, currency),
            actual_balance_minor=to_minor(actual_balance, currency),
            difference_minor=to_minor(actual_balance - expected_balance, currency),
            status=ReconciliationStatus.OPEN,
        )
        self.session.add(sess)
        self.session.flush()
        return sess

    def propose_matches(
        self,
        session_id: int,
        account_id: int,
        statement: list[ParsedTransaction],
    ) -> list[MatchProposal]:
        try:
            from rapidfuzz import fuzz
        except ImportError:  # pragma: no cover
            fuzz = None  # type: ignore[assignment]

        rec_sess = self.session.get(ReconciliationSession, session_id)
        assert rec_sess is not None
        book = self.session.execute(
            select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.posted_date.between(rec_sess.period_start, rec_sess.period_end),
                Transaction.status != TransactionStatus.RECONCILED,
            )
        ).scalars().all()

        proposals: list[MatchProposal] = []
        unmatched_book = list(book)

        for stmt in statement:
            stmt_minor = to_minor(stmt.amount, stmt.currency)
            best: tuple[float, Transaction | None, MatchType] = (0.0, None, MatchType.MANUAL)

            for tx in unmatched_book:
                if tx.currency != stmt.currency:
                    continue
                if tx.amount_minor != stmt_minor:
                    continue
                date_diff = abs((tx.posted_date - stmt.posted_date).days)
                if date_diff > self.date_tolerance.days:
                    continue
                if date_diff == 0 and (tx.description_raw or "") == stmt.description:
                    best = (1.0, tx, MatchType.EXACT)
                    break
                desc_score = (
                    fuzz.token_set_ratio(tx.description_raw or "", stmt.description) / 100.0
                    if fuzz is not None
                    else (1.0 if (tx.description_raw or "") == stmt.description else 0.5)
                )
                date_score = 1.0 - (date_diff / (self.date_tolerance.days + 1))
                score = 0.6 * desc_score + 0.4 * date_score
                if score > best[0]:
                    best = (score, tx, MatchType.FUZZY if score < 1.0 else MatchType.EXACT)

            score, tx, mtype = best
            if tx is not None and score > 0.6:
                unmatched_book.remove(tx)
                proposals.append(
                    MatchProposal(
                        book_transaction_id=tx.id,
                        statement_external_id=stmt.external_id,
                        confidence=score,
                        match_type=mtype,
                    )
                )
            else:
                proposals.append(
                    MatchProposal(
                        book_transaction_id=None,
                        statement_external_id=stmt.external_id,
                        confidence=0.0,
                        match_type=MatchType.MANUAL,
                    )
                )

        return proposals

    def commit_matches(
        self, session_id: int, proposals: list[MatchProposal]
    ) -> int:
        n = 0
        for p in proposals:
            if p.book_transaction_id is None:
                continue
            self.session.add(
                ReconciliationMatch(
                    session_id=session_id,
                    book_transaction_id=p.book_transaction_id,
                    statement_external_id=p.statement_external_id,
                    match_type=p.match_type,
                    confidence=p.confidence,
                )
            )
            tx = self.session.get(Transaction, p.book_transaction_id)
            if tx is not None:
                tx.status = TransactionStatus.RECONCILED
            n += 1
        self.session.flush()
        return n
