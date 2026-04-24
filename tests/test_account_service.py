from finapp.db.base import Base
from finapp.db.seed import seed_all
from finapp.models import Account, Currency, Institution
from finapp.models.enums import AccountType, InstitutionType
from finapp.services.account_service import AccountService


def test_create_institution_and_account(session):
    seed_all(session)

    svc = AccountService(session)
    inst = svc.create_institution("Itaú Test", "BR", InstitutionType.BANK)
    acc = svc.create_account(
        institution_id=inst.id,
        name="CC Itaú",
        account_type=AccountType.CHECKING,
        currency="BRL",
    )

    assert session.get(Account, acc.id) is not None
    assert session.query(Currency).filter_by(code="BRL").one().symbol == "R$"
