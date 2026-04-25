"""Dialog for adding a new account."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from finapp.db.engine import session_scope
from finapp.models.enums import AccountType
from finapp.services.account_service import AccountService
from finapp.services.dto import InstitutionSummary

_ACCOUNT_TYPES = [
    (AccountType.CHECKING, "Conta Corrente"),
    (AccountType.SAVINGS, "Poupança"),
    (AccountType.CREDIT_CARD, "Cartão de Crédito"),
    (AccountType.BROKERAGE, "Corretora"),
    (AccountType.INVESTMENT, "Investimento"),
    (AccountType.LOAN, "Empréstimo"),
    (AccountType.CASH, "Dinheiro"),
    (AccountType.CRYPTO_WALLET, "Carteira Crypto"),
    (AccountType.OTHER, "Outro"),
]

_CURRENCIES = ["BRL", "USD", "EUR", "GBP", "JPY"]


class AddAccountDialog(QDialog):
    def __init__(
        self,
        institutions: list[InstitutionSummary],
        parent: QWidget | None = None,
        preselect_institution_id: int | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova Conta")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.institution_combo = QComboBox()
        for inst in institutions:
            self.institution_combo.addItem(f"{inst.name} ({inst.country})", inst.id)
        if preselect_institution_id is not None:
            for i in range(self.institution_combo.count()):
                if self.institution_combo.itemData(i) == preselect_institution_id:
                    self.institution_combo.setCurrentIndex(i)
                    break
        form.addRow("Instituição:", self.institution_combo)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: Conta Corrente Itaú")
        form.addRow("Nome:", self.name_edit)

        self.type_combo = QComboBox()
        for enum_val, label in _ACCOUNT_TYPES:
            self.type_combo.addItem(label, enum_val)
        form.addRow("Tipo:", self.type_combo)

        self.currency_combo = QComboBox()
        for c in _CURRENCIES:
            self.currency_combo.addItem(c)
        form.addRow("Moeda:", self.currency_combo)

        self.balance_edit = QLineEdit("0.00")
        form.addRow("Saldo Inicial:", self.balance_edit)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Data de Abertura:", self.date_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        try:
            Decimal(self.balance_edit.text().strip().replace(",", "."))
        except (InvalidOperation, ValueError):
            self.balance_edit.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        qdate = self.date_edit.date()
        return {
            "institution_id": self.institution_combo.currentData(),
            "name": self.name_edit.text().strip(),
            "account_type": self.type_combo.currentData(),
            "currency": self.currency_combo.currentText(),
            "opening_balance": Decimal(self.balance_edit.text().strip().replace(",", ".")),
            "opening_date": date(qdate.year(), qdate.month(), qdate.day()),
        }
