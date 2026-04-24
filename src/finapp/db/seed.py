"""Seed data: default currencies, BR/US categories, common institutions."""
from __future__ import annotations

from sqlalchemy.orm import Session

from finapp.models import Category, Currency, Institution
from finapp.models.enums import InstitutionType

DEFAULT_CURRENCIES: list[tuple[str, str, str, int]] = [
    ("BRL", "Real Brasileiro", "R$", 2),
    ("USD", "US Dollar", "$", 2),
    ("EUR", "Euro", "€", 2),
    ("GBP", "British Pound", "£", 2),
    ("JPY", "Japanese Yen", "¥", 0),
]

DEFAULT_CATEGORIES_PT: list[tuple[str, bool]] = [
    ("Receita", True),
    ("Salário", True),
    ("Investimentos - Rendimentos", True),
    ("Moradia", False),
    ("Alimentação", False),
    ("Transporte", False),
    ("Saúde", False),
    ("Educação", False),
    ("Lazer", False),
    ("Impostos", False),
    ("IOF", False),
    ("IR", False),
    ("Investimentos - Aportes", False),
    ("Transferências", False),
]

DEFAULT_INSTITUTIONS: list[tuple[str, str, InstitutionType]] = [
    ("Itaú Unibanco", "BR", InstitutionType.BANK),
    ("Banco do Brasil", "BR", InstitutionType.BANK),
    ("Bradesco", "BR", InstitutionType.BANK),
    ("Nubank", "BR", InstitutionType.BANK),
    ("Inter", "BR", InstitutionType.BANK),
    ("XP Investimentos", "BR", InstitutionType.BROKERAGE),
    ("Rico", "BR", InstitutionType.BROKERAGE),
    ("Chase", "US", InstitutionType.BANK),
    ("Bank of America", "US", InstitutionType.BANK),
    ("Wells Fargo", "US", InstitutionType.BANK),
    ("Fidelity", "US", InstitutionType.BROKERAGE),
    ("Charles Schwab", "US", InstitutionType.BROKERAGE),
    ("Vanguard", "US", InstitutionType.BROKERAGE),
    ("Avenue", "US", InstitutionType.BROKERAGE),
    ("Wise", "US", InstitutionType.OTHER),
]


def seed_all(session: Session) -> None:
    for code, name, symbol, dp in DEFAULT_CURRENCIES:
        if not session.get(Currency, code):
            session.add(Currency(code=code, name=name, symbol=symbol, decimal_places=dp))

    for name, is_income in DEFAULT_CATEGORIES_PT:
        exists = session.query(Category).filter_by(name=name).first()
        if not exists:
            session.add(Category(name=name, is_income=is_income))

    for name, country, itype in DEFAULT_INSTITUTIONS:
        exists = session.query(Institution).filter_by(name=name).first()
        if not exists:
            session.add(Institution(name=name, country=country, type=itype))

    session.flush()
