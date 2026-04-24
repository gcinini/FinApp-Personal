from pathlib import Path

from finapp.db.seed import seed_all
from finapp.integrations.parsers.csv_parser import CsvStatementParser
from finapp.models.enums import AccountType, InstitutionType
from finapp.services.account_service import AccountService
from finapp.services.import_service import ImportService


CSV_BR = """Data,Histórico,Valor,Identificador
01/04/2026,PAGAMENTO PIX MERCADO,-150,50
05/04/2026,SALARIO ACME,12.000,00,EXT-1
06/04/2026,UBER VIAGEM,-32,90,EXT-2
"""


def test_csv_parser_can_detect():
    p = CsvStatementParser()
    assert p.can_parse(Path("foo.csv"))
    assert not p.can_parse(Path("foo.pdf"))


def test_csv_import_end_to_end(tmp_path, session):
    seed_all(session)
    svc = AccountService(session)
    inst = svc.create_institution("Itaú", "BR", InstitutionType.BANK)
    acc = svc.create_account(inst.id, "CC", AccountType.CHECKING, "BRL")

    csv_path = tmp_path / "extrato.csv"
    csv_path.write_text(
        "Data,Histórico,Valor,Identificador\n"
        "01/04/2026,PAGAMENTO PIX,-150.50,EXT-1\n"
        "05/04/2026,SALARIO ACME,12000.00,EXT-2\n"
        "06/04/2026,UBER VIAGEM,-32.90,EXT-3\n",
        encoding="utf-8",
    )

    template = {
        "delimiter": ",",
        "encoding": "utf-8",
        "date_format": "%d/%m/%Y",
        "decimal_separator": ".",
        "thousands_separator": ",",
        "currency": "BRL",
        "columns": {
            "date": "Data",
            "description": "Histórico",
            "amount": "Valor",
            "external_id": "Identificador",
        },
    }

    result = ImportService(session).import_file(csv_path, acc.id, template=template)
    assert result["created"] == 3
    assert result["duplicates"] == 0

    # Re-import is idempotent: file hash matches.
    result2 = ImportService(session).import_file(csv_path, acc.id, template=template)
    assert result2["created"] == 0
