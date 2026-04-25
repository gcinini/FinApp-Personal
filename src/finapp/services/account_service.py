"""Account & transaction services."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finapp.models import Account, Category, Currency, Institution, Transaction
from finapp.models.enums import (
    AccountType,
    InstitutionType,
    TransactionSource,
    TransactionStatus,
)
from finapp.money import to_minor
from finapp.services.dto import (
    AccountSummary,
    CategoryItem,
    CurrencyBalance,
    InstitutionSummary,
    TransactionRow,
)


class AccountService:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ── mutations ────────────────────────────────────────────────────

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

    # ── queries (return DTOs) ────────────────────────────────────────

    def list_institution_summaries(self) -> list[InstitutionSummary]:
        account_count = (
            func.count(Account.id).label("account_count")
        )
        rows = (
            self.session.execute(
                select(
                    Institution.id,
                    Institution.name,
                    Institution.country,
                    Institution.type,
                    account_count,
                )
                .outerjoin(Account, Account.institution_id == Institution.id)
                .group_by(Institution.id)
                .order_by(Institution.country, Institution.name)
            )
            .all()
        )
        return [
            InstitutionSummary(
                id=r.id,
                name=r.name,
                country=r.country,
                type=r.type.value if hasattr(r.type, "value") else str(r.type),
                account_count=r.account_count,
            )
            for r in rows
        ]

    def list_account_summaries(
        self, *, institution_id: int | None = None, active_only: bool = False
    ) -> list[AccountSummary]:
        tx_sum = (
            select(func.coalesce(func.sum(Transaction.amount_minor), 0))
            .where(Transaction.account_id == Account.id)
            .correlate(Account)
            .scalar_subquery()
        )

        stmt = (
            select(
                Account.id,
                Account.name,
                Account.institution_id,
                Institution.name.label("institution_name"),
                Account.account_type,
                Account.currency,
                Currency.symbol.label("currency_symbol"),
                (Account.opening_balance_minor + tx_sum).label("balance_minor"),
                Account.is_active,
            )
            .join(Institution, Institution.id == Account.institution_id)
            .outerjoin(Currency, Currency.code == Account.currency)
            .order_by(Institution.name, Account.name)
        )
        if institution_id is not None:
            stmt = stmt.where(Account.institution_id == institution_id)
        if active_only:
            stmt = stmt.where(Account.is_active.is_(True))

        rows = self.session.execute(stmt).all()
        return [
            AccountSummary(
                id=r.id,
                name=r.name,
                institution_id=r.institution_id,
                institution_name=r.institution_name,
                account_type=r.account_type.value if hasattr(r.account_type, "value") else str(r.account_type),
                currency=r.currency,
                currency_symbol=r.currency_symbol or "",
                balance_minor=r.balance_minor,
                is_active=r.is_active,
            )
            for r in rows
        ]

    def net_worth_by_currency(self) -> list[CurrencyBalance]:
        tx_sum = (
            select(func.coalesce(func.sum(Transaction.amount_minor), 0))
            .where(Transaction.account_id == Account.id)
            .correlate(Account)
            .scalar_subquery()
        )
        stmt = (
            select(
                Account.currency,
                Currency.symbol,
                Currency.decimal_places,
                func.sum(Account.opening_balance_minor + tx_sum).label("total"),
            )
            .outerjoin(Currency, Currency.code == Account.currency)
            .where(Account.is_active.is_(True))
            .group_by(Account.currency)
            .order_by(Account.currency)
        )
        rows = self.session.execute(stmt).all()
        return [
            CurrencyBalance(
                currency=r.currency,
                symbol=r.symbol or "",
                total_minor=r.total or 0,
                decimal_places=r.decimal_places if r.decimal_places is not None else 2,
            )
            for r in rows
        ]


class TransactionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ── mutations ────────────────────────────────────────────────────

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

    _UNSET = object()

    def update(
        self,
        transaction_id: int,
        *,
        posted_date: date | None = None,
        description: str | None = None,
        amount: Decimal | None = None,
        category_id: object = _UNSET,
        memo: object = _UNSET,
        status: TransactionStatus | None = None,
    ) -> Transaction:
        tx = self.session.get(Transaction, transaction_id)
        if tx is None:
            raise ValueError(f"Transaction {transaction_id} not found")
        if tx.status == TransactionStatus.RECONCILED:
            raise ValueError("Cannot edit a reconciled transaction")

        if posted_date is not None:
            tx.posted_date = posted_date
        if description is not None:
            tx.description_raw = description
            tx.description_clean = description
        if amount is not None:
            tx.amount_minor = to_minor(amount, tx.currency)
        if category_id is not TransactionService._UNSET:
            tx.category_id = category_id
        if memo is not TransactionService._UNSET:
            tx.memo = memo
        if status is not None:
            tx.status = status
        self.session.flush()
        return tx

    def delete(self, transaction_id: int) -> None:
        tx = self.session.get(Transaction, transaction_id)
        if tx is None:
            raise ValueError(f"Transaction {transaction_id} not found")
        if tx.status == TransactionStatus.RECONCILED:
            raise ValueError("Cannot delete a reconciled transaction")
        if tx.import_batch_id is not None:
            raise ValueError("Cannot delete an imported transaction — void it instead")
        self.session.delete(tx)
        self.session.flush()

    # ── queries (return DTOs) ────────────────────────────────────────

    def list_transactions(
        self,
        account_id: int,
        *,
        status: TransactionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[TransactionRow]:
        stmt = (
            select(
                Transaction.id,
                Transaction.account_id,
                Account.name.label("account_name"),
                Transaction.posted_date,
                func.coalesce(Transaction.description_clean, Transaction.description_raw).label("description"),
                Category.name.label("category_name"),
                Transaction.amount_minor,
                Transaction.currency,
                Currency.symbol.label("currency_symbol"),
                Transaction.status,
                Transaction.source,
            )
            .join(Account, Account.id == Transaction.account_id)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .outerjoin(Currency, Currency.code == Transaction.currency)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.posted_date.desc(), Transaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            stmt = stmt.where(Transaction.status == status)
        if start_date is not None:
            stmt = stmt.where(Transaction.posted_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(Transaction.posted_date <= end_date)

        rows = self.session.execute(stmt).all()
        return [
            TransactionRow(
                id=r.id,
                account_id=r.account_id,
                account_name=r.account_name,
                posted_date=r.posted_date,
                description=r.description or "",
                category_name=r.category_name,
                amount_minor=r.amount_minor,
                currency=r.currency,
                currency_symbol=r.currency_symbol or "",
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
                source=r.source.value if hasattr(r.source, "value") else str(r.source),
            )
            for r in rows
        ]

    def get_recent(self, *, limit: int = 10) -> list[TransactionRow]:
        stmt = (
            select(
                Transaction.id,
                Transaction.account_id,
                Account.name.label("account_name"),
                Transaction.posted_date,
                func.coalesce(Transaction.description_clean, Transaction.description_raw).label("description"),
                Category.name.label("category_name"),
                Transaction.amount_minor,
                Transaction.currency,
                Currency.symbol.label("currency_symbol"),
                Transaction.status,
                Transaction.source,
            )
            .join(Account, Account.id == Transaction.account_id)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .outerjoin(Currency, Currency.code == Transaction.currency)
            .order_by(Transaction.posted_date.desc(), Transaction.id.desc())
            .limit(limit)
        )
        rows = self.session.execute(stmt).all()
        return [
            TransactionRow(
                id=r.id,
                account_id=r.account_id,
                account_name=r.account_name,
                posted_date=r.posted_date,
                description=r.description or "",
                category_name=r.category_name,
                amount_minor=r.amount_minor,
                currency=r.currency,
                currency_symbol=r.currency_symbol or "",
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
                source=r.source.value if hasattr(r.source, "value") else str(r.source),
            )
            for r in rows
        ]

    def list_categories(self) -> list[CategoryItem]:
        rows = self.session.execute(
            select(Category.id, Category.name, Category.parent_id, Category.is_income)
            .order_by(Category.is_income.desc(), Category.name)
        ).all()
        return [
            CategoryItem(id=r.id, name=r.name, parent_id=r.parent_id, is_income=r.is_income)
            for r in rows
        ]
