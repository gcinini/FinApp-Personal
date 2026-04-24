"""Account & transaction service stubs (Phase 1)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from finapp.models import Account, Institution, Transaction
from finapp.models.enums import AccountType, InstitutionType, TransactionStatus, TransactionSource
from finapp.money import to_minor


class AccountService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_institution(
        self, name: str, country: str, type: InstitutionType
    ) -> Institution:
        inst = Institution(name=name, country=country, type=type)
        self.session.add(inst)
        self.session.flush()
        return inst

    def create_account(
        self,
        institution_id: int,
        name: str,
        account_type: AccountType,
        currency: str,
        opening_balance: Decimal = Decimal(0),
        opening_date: date | None = None,
    ) -> Account:
        acc = Account(
            institution_id=institution_id,
            name=name,
            account_type=account_type,
            currency=currency,
            opening_balance_minor=to_minor(opening_balance, currency),
            opening_date=opening_date,
        )
        self.session.add(acc)
        self.session.flush()
        return acc


class TransactionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(
        self,
        account_id: int,
        posted_date: date,
        amount: Decimal,
        currency: str,
        description: str,
        category_id: int | None = None,
        payee_id: int | None = None,
        memo: str | None = None,
    ) -> Transaction:
        tx = Transaction(
            account_id=account_id,
            posted_date=posted_date,
            amount_minor=to_minor(amount, currency),
            currency=currency,
            description_raw=description,
            description_clean=description,
            category_id=category_id,
            payee_id=payee_id,
            memo=memo,
            status=TransactionStatus.PENDING,
            source=TransactionSource.MANUAL,
        )
        self.session.add(tx)
        self.session.flush()
        return tx
