from decimal import Decimal

from finapp.money import Money, decimals_for, from_minor, to_minor


def test_to_minor_brl():
    assert to_minor(Decimal("12.34"), "BRL") == 1234
    assert to_minor("0.10", "BRL") == 10
    assert to_minor(0, "BRL") == 0


def test_to_minor_jpy_zero_decimals():
    assert decimals_for("JPY") == 0
    assert to_minor(Decimal("1500"), "JPY") == 1500


def test_round_trip():
    m = Money.of("99.99", "USD")
    assert m.amount_minor == 9999
    assert from_minor(m.amount_minor, "USD") == Decimal("99.99")
    assert str(m) == "99.99 USD"
