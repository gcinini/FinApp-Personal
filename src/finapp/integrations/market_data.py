"""Market data provider interface + Yahoo Finance default."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True)
class Quote:
    symbol: str
    price: Decimal
    currency: str
    as_of: date


class MarketDataProvider(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote: ...

    @abstractmethod
    def get_history(self, symbol: str, start: date, end: date) -> list[Quote]: ...


class YahooMarketData(MarketDataProvider):
    def get_quote(self, symbol: str) -> Quote:  # pragma: no cover - network
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        fast = ticker.fast_info
        return Quote(
            symbol=symbol,
            price=Decimal(str(fast["last_price"])),
            currency=fast.get("currency", "USD"),
            as_of=date.today(),
        )

    def get_history(
        self, symbol: str, start: date, end: date
    ) -> list[Quote]:  # pragma: no cover - network
        import yfinance as yf

        df = yf.Ticker(symbol).history(start=start, end=end, auto_adjust=False)
        out: list[Quote] = []
        for ts, row in df.iterrows():
            out.append(
                Quote(
                    symbol=symbol,
                    price=Decimal(str(row["Close"])),
                    currency="USD",
                    as_of=ts.date(),
                )
            )
        return out
