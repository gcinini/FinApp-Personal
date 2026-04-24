"""Money helpers — store amounts as integer minor units paired with an ISO 4217 currency code.

Never use floats for monetary math.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

# Currencies whose minor unit is not 10**2.
_NON_STANDARD_DECIMALS: Final[dict[str, int]] = {
    "JPY": 0,
    "KRW": 0,
    "CLP": 0,
    "BHD": 3,
    "KWD": 3,
    "OMR": 3,
}


def decimals_for(currency: str) -> int:
    return _NON_STANDARD_DECIMALS.get(currency.upper(), 2)


def to_minor(amount: Decimal | str | int | float, currency: str) -> int:
    """Convert a human amount to integer minor units (banker's rounding)."""
    if isinstance(amount, float):
        amount = Decimal(str(amount))
    elif not isinstance(amount, Decimal):
        amount = Decimal(amount)
    factor = Decimal(10) ** decimals_for(currency)
    return int((amount * factor).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def from_minor(minor: int, currency: str) -> Decimal:
    factor = Decimal(10) ** decimals_for(currency)
    return (Decimal(minor) / factor).quantize(Decimal(1) / factor)


@dataclass(frozen=True, slots=True)
class Money:
    amount_minor: int
    currency: str

    @classmethod
    def of(cls, amount: Decimal | str | int | float, currency: str) -> Money:
        return cls(to_minor(amount, currency), currency.upper())

    @property
    def amount(self) -> Decimal:
        return from_minor(self.amount_minor, self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
