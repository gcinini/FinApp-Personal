"""FX rate provider — Banco Central do Brasil (PTAX) default."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True)
class FxQuote:
    base: str
    quote: str
    rate: Decimal
    as_of: date
    source: str


class FxProvider(ABC):
    @abstractmethod
    def get_rate(self, base: str, quote: str, on: date) -> FxQuote: ...


class BcbPtaxProvider(FxProvider):
    """Banco Central do Brasil PTAX (BRL anchor)."""

    BASE_URL = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        "CotacaoDolarDia(dataCotacao=@dataCotacao)"
    )

    def get_rate(self, base: str, quote: str, on: date) -> FxQuote:  # pragma: no cover - network
        import requests

        if {base, quote} != {"BRL", "USD"}:
            raise ValueError("BcbPtaxProvider currently supports BRL<->USD only.")

        params = {
            "@dataCotacao": f"'{on.strftime('%m-%d-%Y')}'",
            "$top": "1",
            "$format": "json",
            "$select": "cotacaoVenda,dataHoraCotacao",
        }
        resp = requests.get(self.BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("value", [])
        if not items:
            raise LookupError(f"No PTAX rate available for {on}")
        usd_brl = Decimal(str(items[0]["cotacaoVenda"]))
        if base == "USD" and quote == "BRL":
            rate = usd_brl
        else:
            rate = Decimal(1) / usd_brl
        return FxQuote(base=base, quote=quote, rate=rate, as_of=on, source="BCB_PTAX")
